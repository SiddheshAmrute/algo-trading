# managers/ledger_manager.py

from db.models import LedgerReport
from utils.db_session import get_db_session
from services.ledger_service import LedgerService
from datetime import datetime, timedelta


class LedgerManager:
    def __init__(self):
        self.service = LedgerService()

    def sync_ledger_to_db(self, from_date: str, to_date: str):
        """
        Syncs ledger report between given dates from Dhan API to Postgres.
        Skips duplicates using (dhan_client_id, voucher_number).
        """
        try:
            data = self.service.fetch_ledger_data(from_date, to_date)
            if not data:
                print("ℹ️ No ledger data to sync.")
                return

            with get_db_session() as session:
                # Get already existing primary keys
                existing_keys = {
                    (row.dhan_client_id, row.voucher_number)
                    for row in session.query(LedgerReport.dhan_client_id, LedgerReport.voucher_number).all()
                }

                new_rows = []
                for row in data:
                    key = (row["dhanClientId"], row["vouchernumber"])
                    if key not in existing_keys:
                        new_rows.append(LedgerReport(
                            dhan_client_id=row["dhanClientId"],
                            narration=row["narration"],
                            voucher_date=row["voucher_date"],
                            exchange=row["exchange"],
                            voucher_desc=row["voucherdesc"],
                            voucher_number=row["vouchernumber"],
                            debit=row["debit"],
                            credit=row["credit"],
                            running_balance=row["running_balance"],
                            created_at=datetime.utcnow()
                        ))

                session.add_all(new_rows)
                print(f"✅ Inserted {len(new_rows)} new ledger records.")

        except Exception as e:
            print(f"❌ Ledger sync failed: {e}")

    def run_incremental(self, full_backfill: bool = False):
        """
        Determines date range:
        - full_backfill: sync from Jan 1, 2022
        - incremental: sync from (last voucher_date + 1) to (today - 1)
        """
        try:
            with get_db_session() as session:
                if full_backfill:
                    start_date = datetime(2022, 1, 1)
                else:
                    last = session.query(LedgerReport.voucher_date).order_by(
                        LedgerReport.voucher_date.desc()).first()
                    start_date = (last[0] + timedelta(days=1)) if last else datetime(2022, 1, 1)

            end_date = datetime.now() - timedelta(days=1)
            if start_date > end_date:
                print("✅ Ledger is already up-to-date.")
                return

            self.sync_ledger_to_db(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        except Exception as e:
            print(f"❌ Ledger incremental load failed: {e}")
