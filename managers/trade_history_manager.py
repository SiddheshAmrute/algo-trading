# managers/trade_history_manager.py

from db.models import TradeHistory
from utils.db_session import get_db_session
from services.trade_history_service import TradeHistoryService
from datetime import datetime, timedelta


class TradeHistoryManager:
    def __init__(self):
        self.service = TradeHistoryService()

    def sync_trade_history_to_db(self, from_date: str, to_date: str):
        """
        Fetches and inserts paginated trade history data.
        Deduplicates using (dhan_client_id, exchange_trade_id).
        """
        try:
            all_inserted = 0
            page = 0

            with get_db_session() as session:
                existing_keys = {
                    (row.dhan_client_id, row.exchange_trade_id)
                    for row in session.query(TradeHistory.dhan_client_id, TradeHistory.exchange_trade_id).all()
                }

            while True:
                data = self.service.fetch_trade_history(from_date, to_date, page)
                if not data:
                    break

                with get_db_session() as session:
                    new_rows = []
                    for row in data:
                        key = (row["dhan_client_id"], row["exchange_trade_id"])
                        if key not in existing_keys:
                            new_rows.append(TradeHistory(**row, created_at=datetime.utcnow()))

                    session.add_all(new_rows)
                    all_inserted += len(new_rows)
                    print(f"📥 Page {page}: Inserted {len(new_rows)} records.")

                page += 1

            print(f"✅ Finished sync. Total inserted: {all_inserted}")

        except Exception as e:
            print(f"❌ Trade history sync failed: {e}")

    def run_incremental(self, full_backfill: bool = False):
        """
        Determines date range:
        - full_backfill: sync from Jan 1, 2022
        - incremental: sync from (last exchange_time + 1) to (today - 1)
        """
        try:
            with get_db_session() as session:
                if full_backfill:
                    start_date = datetime(2022, 1, 1)
                else:
                    last = session.query(TradeHistory.exchange_time).filter(
                        TradeHistory.exchange_time.isnot(None)
                    ).order_by(TradeHistory.exchange_time.desc()).first()
                    start_date = (last[0] + timedelta(days=1)) if last else datetime(2022, 1, 1)

            end_date = datetime.now() - timedelta(days=1)
            if start_date > end_date:
                print("✅ Trade history is already up-to-date.")
                return

            self.sync_trade_history_to_db(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        except Exception as e:
            print(f"❌ Trade history incremental load failed: {e}")
