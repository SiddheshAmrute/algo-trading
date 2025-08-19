from typing import Optional, List
from api.dhan_client import get_trading_client
import requests
import pandas as pd


class DhanTradingAPI:
    def __init__(self):
        self.client = get_trading_client()
        self.client_id = self.client.client_id

    def validate_response(self, response: dict, context: str) -> Optional[dict]:
        if "errorMessage" in response and response["errorMessage"]:
            raise Exception(f"{context} Error: {response['errorMessage']}")
        return response

    # === Fund Related ===
    def get_fund_limit(self) -> Optional[dict]:
        try:
            response = self.client.get("v2/fundlimit")
            return self.validate_response(response, "Fund Limit")
        except Exception as e:
            print(f"❌ Failed to get fund limit: {e}")
            return None

    # === Order Related ===
    def order_placement(self, order_data: dict) -> Optional[dict]:
        try:
            response = self.client.post("v2/orders", payload=order_data)
            return self.validate_response(response, "Order Placement")
        except Exception as e:
            print(f"❌ Failed to place order: {e}")
            return None

    def modify_order(self, order_id: str, modifications: dict) -> Optional[dict]:
        try:
            response = self.client.post(f"v2/orders/{order_id}", payload=modifications)
            return self.validate_response(response, "Order Modify")
        except Exception as e:
            print(f"❌ Failed to modify order {order_id}: {e}")
            return None

    def cancel_order(self, order_id: str) -> Optional[dict]:
        url = f"{self.client.base_url}/v2/orders/{order_id}"
        try:
            response = requests.delete(url, headers=self.client.get_headers())
            response.raise_for_status()
            return self.validate_response(response.json(), "Cancel Order")
        except Exception as e:
            print(f"❌ Failed to cancel order {order_id}: {e}")
            return None

    def slice_order(self, order_data: dict) -> Optional[dict]:
        try:
            response = self.client.post("v2/orders/slicing", payload=order_data)
            return self.validate_response(response, "Sliced Order")
        except Exception as e:
            print(f"❌ Failed to place sliced order: {e}")
            return None

    def get_order_book(self) -> Optional[dict]:
        try:
            response = self.client.get("v2/orders")
            return self.validate_response(response, "Order Book")
        except Exception as e:
            print(f"❌ Failed to fetch order book: {e}")
            return None

    def get_order_by_id(self, order_id: str) -> Optional[dict]:
        try:
            response = self.client.get(f"v2/orders/{order_id}")
            return self.validate_response(response, "Order Fetch")
        except Exception as e:
            print(f"❌ Failed to fetch order {order_id}: {e}")
            return None

    def get_order_by_correlation_id(self, correlation_id: str) -> Optional[dict]:
        try:
            response = self.client.get(f"v2/orders/correlation/{correlation_id}")
            return self.validate_response(response, "Correlation ID")
        except Exception as e:
            print(f"❌ Failed to fetch order by correlation ID {correlation_id}: {e}")
            return None

    # === Trade Related ===
    def get_trade_book(self) -> Optional[dict]:
        try:
            response = self.client.get("v2/orders/trade-book")
            return self.validate_response(response, "Trade Book")
        except Exception as e:
            print(f"❌ Failed to fetch trade book: {e}")
            return None

    def get_trades_by_order_id(self, order_id: str) -> Optional[dict]:
        try:
            response = self.client.get(f"v2/orders/trades/{order_id}")
            return self.validate_response(response, "Trade Fetch")
        except Exception as e:
            print(f"❌ Failed to fetch trades for order {order_id}: {e}")
            return None

    # === Statement Related ===
    def get_ledger_statement(self, from_date: str, to_date: str) -> Optional[pd.DataFrame]:
        try:
            params = {"from-date": from_date, "to-date": to_date}
            response = self.client.get("v2/ledger", params=params)

            if isinstance(response, dict) and response.get("errorMessage"):
                raise Exception(f"Ledger Error: {response['errorMessage']}")

            if not isinstance(response, list) or not response:
                print("ℹ️ No ledger data found.")
                return pd.DataFrame()

            df = pd.DataFrame(response)
            df["voucherdate"] = pd.to_datetime(df["voucherdate"], format="%b %d, %Y")
            df["debit"] = df["debit"].astype(float)
            df["credit"] = df["credit"].astype(float)
            df["runbal"] = df["runbal"].astype(float)

            return df

        except Exception as e:
            print(f"❌ Failed to fetch ledger statement: {e}")
            return None

    def fetch_trade_history_from_api(self, from_date: str, to_date: str, page: int = 0) -> List[dict]:
        """
        Calls the Dhan Trade History API and returns a list of dicts.
        Consistent with fetch_ledger_report_from_api().
        """
        try:
            endpoint = f"v2/trades/{from_date}/{to_date}/{page}"
            response = self.client.get(endpoint)

            if isinstance(response, dict) and response.get("errorMessage"):
                raise Exception(f"Dhan API Error: {response['errorMessage']}")

            if isinstance(response, list):
                return response

            print("⚠️ Unexpected response format for trade history.")
            return []

        except Exception as e:
            print(f"❌ Failed to fetch trade history: {e}")
            return []

    def fetch_ledger_report_from_api(self, from_date: str, to_date: str) -> List[dict]:
        try:
            response = self.client.get("v2/ledger", params={
                "from-date": from_date,
                "to-date": to_date
            })

            if isinstance(response, dict) and response.get("errorMessage"):
                raise Exception(f"Dhan API Error: {response['errorMessage']}")

            if isinstance(response, list):
                return response

            print("⚠️ Unexpected response format for ledger report.")
            return []

        except Exception as e:
            print(f"❌ Failed to fetch ledger report: {e}")
            return []

