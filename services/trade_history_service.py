# services/trade_history_service.py

from api.trading_api import DhanTradingAPI
from datetime import datetime
from typing import List
import pandas as pd


class TradeHistoryService:
    def __init__(self):
        self.api = DhanTradingAPI()

    def fetch_trade_history(self, from_date: str, to_date: str, page: int = 0) -> List[dict]:
        """
        Fetches raw trade history using new API wrapper and transforms into model-ready dicts.
        """
        raw_data = self.api.fetch_trade_history_from_api(from_date, to_date, page)
        if not raw_data:
            return []

        processed = []
        for item in raw_data:
            try:
                processed.append({
                    "dhan_client_id": item.get("dhanClientId"),
                    "order_id": item.get("orderId"),
                    "exchange_order_id": item.get("exchangeOrderId"),
                    "exchange_trade_id": item.get("exchangeTradeId"),
                    "transaction_type": item.get("transactionType"),
                    "exchange_segment": item.get("exchangeSegment"),
                    "product_type": item.get("productType"),
                    "order_type": item.get("orderType"),
                    "trading_symbol": item.get("tradingSymbol"),
                    "custom_symbol": item.get("customSymbol"),
                    "security_id": item.get("securityId"),
                    "traded_quantity": int(item.get("tradedQuantity", 0)),
                    "traded_price": float(item.get("tradedPrice", 0)),
                    "isin": item.get("isin"),
                    "instrument": item.get("instrument"),
                    "sebi_tax": float(item.get("sebiTax", 0)),
                    "stt": float(item.get("stt", 0)),
                    "brokerage_charges": float(item.get("brokerageCharges", 0)),
                    "service_tax": float(item.get("serviceTax", 0)),
                    "exchange_transaction_charges": float(item.get("exchangeTransactionCharges", 0)),
                    "stamp_duty": float(item.get("stampDuty", 0)),
                    "exchange_time": pd.to_datetime(item.get("exchangeTime"), errors="coerce"),
                    "drv_expiry_date": item.get("drvExpiryDate") if item.get("drvExpiryDate") != "NA" else None,
                    "drv_option_type": item.get("drvOptionType") if item.get("drvOptionType") != "NA" else None,
                    "drv_strike_price": float(item.get("drvStrikePrice", 0))
                })
            except Exception as e:
                print(f"⚠️ Failed to parse trade row: {e}")
        return processed

