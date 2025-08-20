# services/ledger_service.py

from api.trading_api import DhanTradingAPI
from datetime import datetime
from typing import List


class LedgerService:
    def __init__(self):
        self.api = DhanTradingAPI()

    def fetch_ledger_data(self, from_date: str, to_date: str) -> List[dict]:
        """
        Fetches ledger entries from Dhan API between two dates.
        Converts amounts to float and voucherdate to datetime.
        """
        raw_data = self.api.fetch_ledger_report_from_api(from_date, to_date)
        if not raw_data:
            return []

        processed = []
        for item in raw_data:
            try:
                item["voucher_date"] = datetime.strptime(item["voucherdate"], "%b %d, %Y")
                item["debit"] = float(item.get("debit", 0.0))
                item["credit"] = float(item.get("credit", 0.0))
                item["running_balance"] = float(item.get("runbal", 0.0))
                processed.append(item)
            except Exception as e:
                print(f"⚠️ Failed to process ledger row: {e} | Data: {item}")
        return processed
