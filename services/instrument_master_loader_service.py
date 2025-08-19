import pandas as pd
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from utils.db_session import get_db_session
from db.models import InstrumentMaster, AllInstrumentsList
from utils.telegram_notifier import send_telegram_message


class InstrumentMasterLoaderService:
    def __init__(self):
        self.today = datetime.now().date()

    def load_instrument_master(self):
        try:
            with get_db_session() as session:
                df = pd.read_sql(session.query(AllInstrumentsList).statement, session.bind)

            # Rename columns for clarity
            df.rename(columns={
                "sem_exm_exch_id": "exchange",
                "sem_segment": "segment",
                "sem_instrument_name": "instrument",
                "sem_expiry_code": "expiry_code",
                "sem_expiry_flag": "expiry_flag",
                "sem_expiry_date": "expiry_date",
                "sem_option_type": "option_type",
                "sem_strike_price": "strike_price",
                "sem_lot_units": "lot_size",
                "sem_series": "series",
                "sem_exch_instrument_type": "exch_instrument_type",
                "sem_trading_symbol": "sem_trading_symbol",
                "sem_custom_symbol": "sem_custom_symbol",
                "sem_smst_security_id": "security_id",
                "sm_symbol_name": "underlying"
            }, inplace=True)

            commodity_list = ['NATURALGAS', 'NATGASMINI', 'CRUDEOIL', 'CRUDEOILM', 'SILVER', 'SILVERM', 'SILVERMIC', 'GOLD', 'GOLDM', 'GOLDGUINEA', 'GOLDPETAL', 'GOLDTEN']

            # Filter relevant instruments
            df = df[
                ((df["exchange"] == "NSE") & (df["segment"] == "I") & (df["exch_instrument_type"] == "INDEX")) |
                ((df["exchange"] == "NSE") & (df["segment"] == "E") & (df["series"] == "EQ")) |
                ((df["exchange"] == "NSE") & (df["segment"] == "D") & (df["exch_instrument_type"] == "OP")) |
                ((df["exchange"] == "NSE") & (df["segment"] == "D") & (df["exch_instrument_type"] == "FUT")) |
                ((df["exchange"] == "MCX") & (df["segment"] == "M") & df["sem_custom_symbol"].isin(commodity_list))
            ]

            # Map Segment to Segment Names
            segment_map = {
                "E": "Equity",
                "D": "Derivatives",
                "M": "Commodity",
                "I": "Index"
            }
            df["segment"] = df["segment"].map(segment_map)

            # Assign trading symbol
            df["trading_symbol"] = df.apply(
                lambda row: row["sem_custom_symbol"]
                if row["segment"] in ["Derivatives", "Commodity"]
                else row["sem_trading_symbol"],
                axis=1
            )

            # Assign exchange segment
            def resolve_segment(row):
                if row["exchange"] == "NSE":
                    if row["segment"] == "Equity":
                        return "NSE_EQ"
                    elif row["segment"] == "Derivatives":
                        return "NSE_FNO"
                    elif row["segment"] == "Index":
                        return "IDX_I"
                elif row["exchange"] == "MCX" and row["segment"] == "Commodity":
                    return "MCX_COMM"
                return None

            df["exchange_segment"] = df.apply(resolve_segment, axis=1)

            # Utility function to extract underlying from custom symbol
            def extract_underlying(symbol: str) -> str:
                if isinstance(symbol, str):
                    return symbol.split()[0]
                return None

            # Extract underlying from custom_symbol if segment is Derivatives or Commodity
            mask = df["segment"].isin(["Derivatives"])
            df.loc[mask, "underlying"] = df.loc[mask, "sem_custom_symbol"].apply(extract_underlying)

            # Convert expiry_date
            df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce")
            df["expiry_date"] = df["expiry_date"].apply(lambda x: x.date() if pd.notnull(x) else None)

            df["security_id"] = df["security_id"].astype(int)
            df["strike_price"] = pd.to_numeric(df["strike_price"], errors="coerce")
            df["lot_size"] = pd.to_numeric(df["lot_size"], errors="coerce").fillna(0).astype(int)

            # Set expiry_code = None for Equity and Index instruments
            df.loc[df["segment"].isin(["Equity", "Index"]), "expiry_code"] = None

            # Only fillna(0) and convert for Derivatives
            df.loc[df["segment"] == "Derivatives", "expiry_code"] = pd.to_numeric(
                df.loc[df["segment"] == "Derivatives", "expiry_code"], errors="coerce"
            ).fillna(0).astype(int)

            # Replace null-like values
            df = df.replace({pd.NA: None, pd.NaT: None, float("nan"): None, "NaT": None, "nan": None})
            df["created_at"] = datetime.utcnow()

            # Calculate expiry_code for NSE Derivatives by grouping on instrument, underlying, expiry_flag
            derivatives_df = df[
                (df["exchange"] == "NSE") &
                (df["segment"] == "Derivatives") &
                (df["expiry_date"].notnull())
                ]

            # Sort and rank expiry dates within each group
            derivatives_df = derivatives_df.sort_values(by=["instrument", "underlying", "expiry_flag", "expiry_date"])
            derivatives_df["expiry_code"] = (
                    derivatives_df.groupby(["instrument", "underlying", "expiry_flag"])["expiry_date"]
                    .rank(method="dense").astype(int) - 1
            )

            # Merge back the updated expiry_code into the main DataFrame
            df.update(derivatives_df[["expiry_code"]])

            # Prepare records for insert
            records = df[[
                "security_id", "underlying", "trading_symbol", "exchange", "exchange_segment", "segment",
                "instrument", "expiry_code", "expiry_flag", "expiry_date", "option_type",
                "strike_price", "lot_size", "created_at"
            ]].to_dict(orient="records")

            with get_db_session() as session:
                session.execute(text("TRUNCATE TABLE instrument_master RESTART IDENTITY"))
                session.bulk_insert_mappings(InstrumentMaster, records)
                print(f"✅ Loaded {len(records)} records into instrument_master")

            return len(records)

        except SQLAlchemyError as e:
            error_msg = f"❌ Database error while loading instrument master\n🔍 Error: {e}"
            print(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            error_msg = f"❌ Unexpected error during instrument master load\n🔍 Error: {e}"
            print(error_msg)
            raise Exception(error_msg)
