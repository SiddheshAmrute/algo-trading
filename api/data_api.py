# api/data_api.py

import pandas as pd
from datetime import datetime
from typing import Optional
import time
from api.dhan_client import get_data_client
from utils.db_session import get_db_session
from db.models import InstrumentMaster
from utils.telegram_notifier import send_telegram_message


from sqlalchemy import or_


def get_security_details_from_db(trading_symbols: list[str]) -> dict:
    """
    Fetch instrument metadata from PostgreSQL for the provided trading symbols or underlying names.
    """
    normalized_symbols = [s.strip().upper() for s in trading_symbols]

    with get_db_session() as session:
        rows = session.query(InstrumentMaster).filter(
            or_(
                InstrumentMaster.trading_symbol.in_(normalized_symbols),
                InstrumentMaster.underlying.in_(normalized_symbols)
            )
        ).all()

        return {
            row.trading_symbol.strip().upper(): {
                "security_id": row.security_id,
                "exchange": row.exchange,
                "exchange_segment": row.exchange_segment,
                "instrument": row.instrument,
                "expiry_code": row.expiry_code,
                "underlying": row.underlying.strip().upper() if row.underlying else row.trading_symbol.strip().upper()
            }
            for row in rows
        }


class DhanDataAPI:
    def __init__(self):
        self.dhan_data = get_data_client()
        self._option_chain_cache = {}

    @staticmethod
    def convert_to_date_time(epoch: int) -> datetime:
        return datetime.fromtimestamp(epoch if epoch < 1e12 else epoch / 1000)

    def get_ltp_for_instruments(self, trading_symbols: list[str]) -> Optional[dict]:
        """
        Fetch LTPs using marketfeed/ltp. If unavailable, fallback to last hourly close.
        """
        try:
            metadata = get_security_details_from_db(trading_symbols)

            instrument_map = {}
            id_to_symbol = {}
            fallback_needed = set()

            for symbol, meta in metadata.items():
                segment = meta["exchange_segment"]
                sec_id = str(meta["security_id"])
                instrument_map.setdefault(segment, []).append(int(sec_id))
                id_to_symbol[(segment, sec_id)] = symbol

            result = {}

            # Step 1: Try fetching live LTP
            try:
                response = self.dhan_data.post("v2/marketfeed/ltp", payload=instrument_map)
                if response and "data" in response:
                    for segment, segment_data in response["data"].items():
                        for sec_id, info in segment_data.items():
                            key = (segment, sec_id)
                            symbol = id_to_symbol.get(key)
                            price = info.get("last_price")
                            if symbol and price is not None:
                                result[symbol] = price
                            else:
                                fallback_needed.add(symbol)
                else:
                    fallback_needed.update(trading_symbols)

            except Exception as e:
                print(f"⚠️ LTP fetch failed, falling back to hourly close: {e}")
                fallback_needed.update(trading_symbols)

            # Step 2: Fallback to last hourly close
            if fallback_needed:
                from datetime import timedelta
                today = datetime.now()
                from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                to_date = today.strftime("%Y-%m-%d %H:%M:%S")

                for symbol in fallback_needed:
                    try:
                        df = self.get_intraday_historical_data(
                            trading_symbol=symbol,
                            interval=60,  # 1-hour candle
                            from_date=from_date,
                            to_date=to_date
                        )
                        if not df.empty:
                            result[symbol] = df["close"].dropna().iloc[-1]
                    except Exception as ex:
                        print(f"⚠️ Fallback failed for {symbol}: {ex}")

            return result if result else None

        except Exception as e:
            print(f"❌ Error in get_ltp_for_instruments: {e}")
            send_telegram_message(f"❌ LTP Fetch Error: {e}", parse_mode=None)
            return None

    def get_historical_data(
            self,
            trading_symbol: str,
            interval: str,
            from_date: str,
            to_date: str,
            alert: bool = True
    ) -> pd.DataFrame:
        """
        Unified function to fetch historical OHLC data for any interval.

        Args:
            trading_symbol (str): Symbol from instrument_master
            interval (str): "1", "5", "15", "30", "60", "D", "W", "M"
            from_date (str): 'YYYY-MM-DD HH:MM:SS'
            to_date (str): 'YYYY-MM-DD HH:MM:SS'
            alert (bool): Send Telegram alert on failure

        Returns:
            pd.DataFrame
        """
        try:
            meta = get_security_details_from_db([trading_symbol]).get(trading_symbol)
            if not meta:
                raise ValueError(f"Instrument metadata not found for: {trading_symbol}")

            time.sleep(1)

            payload = {
                "securityId": str(meta["security_id"]),
                "exchangeSegment": meta["exchange_segment"],
                "instrument": meta["instrument"],
                "oi": False,
                "fromDate": from_date,
                "toDate": to_date,
            }

            interval_upper = interval.upper()
            if interval.upper() in ["D", "W", "M"]:
                expiry_code = meta.get("expiry_code")
                if expiry_code is not None:
                    payload["expiryCode"] = int(expiry_code)

                response = self.dhan_data.post("v2/charts/historical", payload)

                if not response or "timestamp" not in response:
                    raise ValueError(f"No data returned for {trading_symbol}")

                df = pd.DataFrame({
                    "timestamp": [self.convert_to_date_time(ts) for ts in response["timestamp"]],
                    "open": response["open"],
                    "high": response["high"],
                    "low": response["low"],
                    "close": response["close"],
                    "volume": response["volume"],
                    "open_interest": response.get("open_interest", [0] * len(response["timestamp"]))
                })

                if interval_upper == "W":
                    df = self._resample_ohlc(df, 'W')
                    print(f"✅ Retrieved {len(df)} weekly candles for {trading_symbol}")
                    return df
                elif interval_upper == "M":
                    df = self._resample_ohlc(df, 'M')
                    print(f"✅ Retrieved {len(df)} monthly candles for {trading_symbol}")
                    return df
                else:
                    print(f"✅ Retrieved {len(df)} daily candles for {trading_symbol}")
                    return df

            else:
                # Intraday case
                payload["interval"] = str(interval)
                response = self.dhan_data.post("v2/charts/intraday", payload)

                if not response or "timestamp" not in response:
                    raise ValueError(f"No data returned for {trading_symbol}")

                df = pd.DataFrame({
                    "timestamp": [self.convert_to_date_time(ts) for ts in response["timestamp"]],
                    "open": response["open"],
                    "high": response["high"],
                    "low": response["low"],
                    "close": response["close"],
                    "volume": response["volume"],
                    "open_interest": response.get("open_interest", [0] * len(response["timestamp"]))
                })

            return df

        except Exception as e:
            msg = f"❌ Historical OHLC Error for {trading_symbol}: {e}"
            print(msg)
            if alert:
                send_telegram_message(msg)
            return pd.DataFrame()

    def _resample_ohlc(self, df: pd.DataFrame, rule: str) -> pd.DataFrame:
        """
        Resample daily candles to weekly/monthly using OHLC aggregation logic.

        Args:
            df (pd.DataFrame): Daily data
            rule (str): 'W' or 'M'

        Returns:
            pd.DataFrame
        """
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'open_interest': 'last'
        }

        df_resampled = df.resample(rule).agg(agg_dict).dropna().reset_index()
        return df_resampled

    def get_daily_historical_data(
            self,
            trading_symbol: str,
            from_date: str,
            to_date: str,
            alert: bool = True
    ) -> pd.DataFrame:
        """
        Fetch daily OHLC historical data using trading symbol from instrument_master.

        Args:
            trading_symbol (str): Symbol from instrument_master (must be unique).
            from_date (str): Start date in 'YYYY-MM-DD' format.
            to_date (str): End date in 'YYYY-MM-DD' format.
            alert (bool): Whether to send Telegram alerts on failure.

        Returns:
            pd.DataFrame: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
        """
        try:
            # Step 1: Get instrument metadata from DB
            meta = get_security_details_from_db([trading_symbol]).get(trading_symbol)
            if not meta:
                raise ValueError(f"Instrument metadata not found for: {trading_symbol}")

            # Step 2: Prepare API payload
            payload = {
                "securityId": str(meta["security_id"]),
                "exchangeSegment": meta["exchange_segment"],
                "instrument": meta["instrument"],
                "expiryCode": int(meta["expiry_code"]),
                "oi": False,
                "fromDate": from_date,
                "toDate": to_date
            }

            # Step 3: Hit Dhan API
            time.sleep(1)  # rate limiting
            response = self.dhan_data.post("v2/charts/historical", payload)

            if not response or not response.get("timestamp"):
                raise ValueError(f"No data returned for {trading_symbol}")

            # Step 4: Structure result into DataFrame
            df = pd.DataFrame({
                "timestamp": [self.convert_to_date_time(ts) for ts in response["timestamp"]],
                "open": response["open"],
                "high": response["high"],
                "low": response["low"],
                "close": response["close"],
                "volume": response["volume"],
                "open_interest": response.get("open_interest", [0] * len(response["timestamp"]))
            })

            return df

        except Exception as e:
            error_msg = f"❌ Daily OHLC Error for {trading_symbol}: {e}"
            print(error_msg)
            if alert:
                send_telegram_message(error_msg, parse_mode=None)
            return pd.DataFrame()

    def get_intraday_historical_data(self, trading_symbol: str, interval: int, from_date: str,
                                     to_date: str) -> pd.DataFrame:
        """
        Fetch intraday historical OHLC data for a given trading symbol.

        Args:
            trading_symbol (str): Symbol as per instrument_master table (e.g., "RELIANCE")
            interval (int): Candle interval in minutes (1, 5, 15, 30, 60)
            from_date (str): Start datetime in 'YYYY-MM-DD HH:MM:SS'
            to_date (str): End datetime in 'YYYY-MM-DD HH:MM:SS'

        Returns:
            pd.DataFrame: Intraday OHLC data or empty DataFrame on error
        """
        try:
            # Step 1: Fetch metadata from DB
            meta = get_security_details_from_db([trading_symbol]).get(trading_symbol)
            if not meta:
                raise Exception(f"Instrument metadata not found for: {trading_symbol}")

            # Step 2: Construct API payload
            payload = {
                "securityId": str(meta["security_id"]),
                "exchangeSegment": meta["exchange_segment"],
                "instrument": meta["instrument"],
                "interval": str(interval),
                "oi": False,
                "fromDate": from_date,
                "toDate": to_date
            }

            time.sleep(1)  # API rate limit buffer
            resp = self.dhan_data.post("v2/charts/intraday", payload)

            if not resp:
                print(f"⚠️ No intraday data returned for {trading_symbol}")
                return pd.DataFrame()

            return pd.DataFrame({
                "timestamp": [self.convert_to_date_time(ts) for ts in resp["timestamp"]],
                "open": resp["open"],
                "high": resp["high"],
                "low": resp["low"],
                "close": resp["close"],
                "volume": resp["volume"],
                "open_interest": resp.get("open_interest", [0] * len(resp["timestamp"]))
            })

        except Exception as e:
            send_telegram_message(f"❌ Intraday OHLC Error for {trading_symbol}: {e}", parse_mode=None)
            return pd.DataFrame()

    # === get_ohlc_for_instruments ===
    def get_ohlc_for_instruments(self, trading_symbols: list[str]) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC + LTP data for a list of trading symbols using metadata from instrument_master.

        Args:
            trading_symbols (list[str]): Trading symbols (must exist in instrument_master)

        Returns:
            Optional[pd.DataFrame]: Columns - trading_symbol, last_price, open, high, low, close
        """
        try:
            metadata_map = get_security_details_from_db(trading_symbols)

            instrument_map = {}
            id_to_symbol = {}

            for symbol, meta in metadata_map.items():
                segment = meta["exchange_segment"]
                sec_id = str(meta["security_id"])
                instrument_map.setdefault(segment, []).append(int(sec_id))
                id_to_symbol[(segment, sec_id)] = symbol

            if not instrument_map:
                print("⚠️ No valid instruments to fetch OHLC.")
                return None

            response = self.dhan_data.post("v2/marketfeed/ohlc", payload=instrument_map)

            if not response or "data" not in response:
                print("⚠️ No OHLC data found in response.")
                return None

            records = []
            for segment, segment_data in response["data"].items():
                for sec_id, sec_info in segment_data.items():
                    symbol = id_to_symbol.get((segment, sec_id))
                    if symbol:
                        ohlc = sec_info.get("ohlc", {})
                        records.append({
                            "trading_symbol": symbol,
                            "last_price": sec_info.get("last_price"),
                            "open": ohlc.get("open"),
                            "high": ohlc.get("high"),
                            "low": ohlc.get("low"),
                            "close": ohlc.get("close")
                        })

            df = pd.DataFrame(records)
            return df if not df.empty else None

        except Exception as e:
            print(f"❌ Error in get_ohlc_for_instruments: {e}")
            send_telegram_message(f"❌ OHLC Fetch Error: {e}", parse_mode=None)
            return None

    def get_market_depth_for_instruments(self, trading_symbols: list[str]) -> Optional[pd.DataFrame]:
        try:
            metadata_map = get_security_details_from_db(trading_symbols)

            instrument_map = {}
            id_to_symbol = {}

            for symbol, meta in metadata_map.items():
                segment = meta["exchange_segment"]
                sec_id = str(meta["security_id"])
                instrument_map.setdefault(segment, []).append(int(sec_id))
                id_to_symbol[(segment, sec_id)] = symbol

            if not instrument_map:
                print("⚠️ No valid instruments to fetch market depth.")
                return None

            time.sleep(1)  # Rate limit
            response = self.dhan_data.post("v2/marketfeed/quote", payload=instrument_map)

            if not response or "data" not in response:
                print("⚠️ No market depth data found.")
                return None

            records = []
            for segment, segment_data in response["data"].items():
                for sec_id, sec_info in segment_data.items():
                    symbol = id_to_symbol.get((segment, sec_id))
                    if symbol:
                        ohlc = sec_info.get("ohlc", {})
                        depth = sec_info.get("depth", {})
                        buy_levels = depth.get("buy", [])
                        sell_levels = depth.get("sell", [])

                        record = {
                            "trading_symbol": symbol,
                            "last_price": sec_info.get("last_price"),
                            "average_price": sec_info.get("average_price"),
                            "net_change": sec_info.get("net_change"),
                            "volume": sec_info.get("volume"),
                            "open": ohlc.get("open"),
                            "high": ohlc.get("high"),
                            "low": ohlc.get("low"),
                            "close": ohlc.get("close"),
                            "buy_quantity_total": sec_info.get("buy_quantity"),
                            "sell_quantity_total": sec_info.get("sell_quantity"),
                            "lower_circuit_limit": sec_info.get("lower_circuit_limit"),
                            "upper_circuit_limit": sec_info.get("upper_circuit_limit"),
                            "oi": sec_info.get("oi"),
                            "oi_day_high": sec_info.get("oi_day_high"),
                            "oi_day_low": sec_info.get("oi_day_low"),
                            "last_trade_time": sec_info.get("last_trade_time")
                        }

                        for i in range(5):
                            record[f"bid_price_{i + 1}"] = buy_levels[i]["price"] if i < len(buy_levels) else None
                            record[f"bid_qty_{i + 1}"] = buy_levels[i]["quantity"] if i < len(buy_levels) else None
                            record[f"ask_price_{i + 1}"] = sell_levels[i]["price"] if i < len(sell_levels) else None
                            record[f"ask_qty_{i + 1}"] = sell_levels[i]["quantity"] if i < len(sell_levels) else None

                        records.append(record)

            df = pd.DataFrame(records)
            return df if not df.empty else None

        except Exception as e:
            print(f"❌ Error in get_market_depth_for_instruments: {e}")
            send_telegram_message(f"❌ Market Depth Error: {e}", parse_mode=None)
            return None

    # === Option Chain ===
    def flatten_option_chain_data(self, data: dict) -> pd.DataFrame:
        """
        Flatten the nested option chain data from Dhan API into a structured pandas DataFrame.

        Args:
            data (dict): Raw option chain response data block from API, with CE/PE info per strike.

        Returns:
            pd.DataFrame: Flattened option chain with CE and PE metrics side by side per strike
        """
        # Step 1: Extract core data blocks
        oc_data = data.get("oc", {})                 # Option chain data per strike
        last_price = data.get("last_price", None)   # Underlying LTP

        records = []

        # Step 2: Iterate through each strike and process CE/PE data
        for strike_str, strike_data in oc_data.items():
            strike = float(strike_str)

            # Extract Call and Put data
            ce = strike_data.get("ce", {})
            pe = strike_data.get("pe", {})

            # Step 3: Build flat row with all metrics
            record = {
                "strike": strike,
                "underlying_ltp": last_price,

                # Call Option Fields
                "ce_last_price": ce.get("last_price"),
                "ce_iv": ce.get("implied_volatility"),
                "ce_oi": ce.get("oi"),
                "ce_volume": ce.get("volume"),
                "ce_delta": ce.get("greeks", {}).get("delta"),
                "ce_theta": ce.get("greeks", {}).get("theta"),
                "ce_gamma": ce.get("greeks", {}).get("gamma"),
                "ce_vega": ce.get("greeks", {}).get("vega"),

                # Put Option Fields
                "pe_last_price": pe.get("last_price"),
                "pe_iv": pe.get("implied_volatility"),
                "pe_oi": pe.get("oi"),
                "pe_volume": pe.get("volume"),
                "pe_delta": pe.get("greeks", {}).get("delta"),
                "pe_theta": pe.get("greeks", {}).get("theta"),
                "pe_gamma": pe.get("greeks", {}).get("gamma"),
                "pe_vega": pe.get("greeks", {}).get("vega"),
            }

            records.append(record)

        # Step 4: Convert to DataFrame and sort by strike
        df = pd.DataFrame(records)
        df.sort_values("strike", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    def get_expiry_list(self, trading_symbol: str, exchange: str, instrument: str) -> Optional[list[str]]:
        """
        Fetch available expiry dates for a given underlying symbol using Dhan Option Chain API.

        Args:
            trading_symbol (str): Name of the underlying (e.g., "BANKNIFTY", "RELIANCE")
            exchange (str): Exchange code (e.g., "NSE")
            instrument (str): Instrument type (e.g., "OPTIDX", "OPTSTK")

        Returns:
            Optional[list[str]]: List of expiry dates in 'YYYY-MM-DD' format, or None on failure.
        """
        try:
            # Fetch security details from DB
            info = get_security_details_from_db([trading_symbol]).get(trading_symbol)
            if not info:
                raise ValueError(f"Security details not found for: {trading_symbol}")

            payload = {
                "UnderlyingScrip": info["security_id"],
                "UnderlyingSeg": info["exchange_segment"]
            }
            print(payload)
            response = self.dhan_data.post("v2/optionchain/expirylist", payload)

            if response["status"] == "success" and "data" in response:
                return response["data"]
            else:
                print(f"⚠️ No expiry dates found in response for {trading_symbol}")
                return None

        except Exception as e:
            print(f"❌ Exception in get_expiry_list: {e}")
            send_telegram_message(f"❌ Failed to fetch expiry list for {trading_symbol}: {e}")
            return None

    def get_expiry_by_index(self, trading_symbol: str, exchange: str, instrument: str, index: int = 0) -> Optional[str]:
        """
        Fetch a specific expiry date by index from the expiry list.
        
        Args:
            trading_symbol (str): Underlying symbol name (e.g., "BANKNIFTY", "RELIANCE")
            exchange (str): Exchange code (e.g., "NSE")
            instrument (str): Instrument type (e.g., "OPTIDX", "OPTSTK")
            index (int): Index of expiry date to fetch (0 = nearest expiry)

        Returns:
            Optional[str]: Expiry date in 'YYYY-MM-DD' format, or None if not available
        """
        try:
            expiry_list = self.get_expiry_list(trading_symbol, exchange, instrument)

            if expiry_list and 0 <= index < len(expiry_list):
                return expiry_list[index]

            print(f"⚠️ Invalid expiry index ({index}) for {trading_symbol}.")
            return None

        except Exception as e:
            send_telegram_message(f"❌ Failed to fetch expiry by index for {trading_symbol}: {e}")
            print(f"❌ Exception in get_expiry_by_index: {e}")
            return None

    def get_option_chain_data(self, trading_symbol: str, exchange: str, instrument: str, expiry_index: int = 0) -> Optional[pd.DataFrame]:
        """
        Fetch and flatten the option chain data for a given underlying symbol and expiry index.

        Args:
            trading_symbol (str): Underlying symbol name (e.g., "BANKNIFTY", "RELIANCE")
            exchange (str): Exchange code (e.g., "NSE", "BSE")
            instrument (str): Instrument type (e.g., "OPTIDX", "OPTSTK")
            expiry_index (int): Index of the expiry date (0 = nearest expiry, 1 = next, etc.)

        Returns:
            Optional[pd.DataFrame]: Flattened option chain DataFrame or None on failure.
        """
        try:
            # Step 1: Get expiry date from index
            expiry = self.get_expiry_by_index(trading_symbol, exchange, instrument, expiry_index)
            if not expiry:
                print(f"⚠️ Expiry index {expiry_index} invalid or not found for {trading_symbol}.")
                return None

            # Step 2: Resolve security details from DB
            info = get_security_details_from_db([trading_symbol]).get(trading_symbol)
            if not info:
                raise ValueError(f"Security details not found for {trading_symbol}")

            # Step 3: Prepare request payload
            payload = {
                "underlyingScrip": info["security_id"],
                "underlyingSeg": info["exchange_segment"],
                "expiry": expiry
            }

            # Step 4: Make POST request
            response = self.dhan_data.post("v2/optionchain", payload)
            time.sleep(3)

            # Step 5: Validate and flatten response
            if "data" not in response or "oc" not in response["data"]:
                print(f"⚠️ No option chain data returned for {trading_symbol}.")
                return None

            df = self.flatten_option_chain_data(response["data"])

            # Optionally include expiry for downstream usage
            df["expiry"] = expiry
            df["symbol"] = trading_symbol

            return df

        except Exception as e:
            send_telegram_message(f"❌ Failed to fetch option chain data for {trading_symbol}: {e}")
            print(f"❌ Exception in get_option_chain_data: {e}")
            return None

    def get_cached_option_chain(self, trading_symbol: str, exchange: str, instrument: str, expiry_index: int = 0) -> \
    Optional[pd.DataFrame]:
        """
        Cached version of get_option_chain_data to avoid redundant API calls.
        """
        cache_key = (trading_symbol, expiry_index)

        if cache_key in self._option_chain_cache:
            return self._option_chain_cache[cache_key]

        # Call actual function
        df = self.get_option_chain_data(trading_symbol, exchange, instrument, expiry_index)
        if df is not None and not df.empty:
            self._option_chain_cache[cache_key] = df

        return df
