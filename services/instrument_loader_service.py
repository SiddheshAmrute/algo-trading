import os
from pathlib import Path
import shutil
import requests
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from utils.db_session import get_db_session
from db.models import AllInstrumentsList
from utils.telegram_notifier import send_telegram_message


class InstrumentLoaderService:
    def __init__(self):
        self.url = "https://images.dhan.co/api-data/api-scrip-master.csv"
        project_root = Path(__file__).resolve().parent.parent

        self.base_dir = project_root / "dependencies"
        self.archive_dir = self.base_dir / "archive"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.today = datetime.now().date()
        self.filename = f"instrument_{self.today.strftime('%Y_%m_%d')}.csv"

        self.local_file = self.base_dir / self.filename

    def already_downloaded_today(self) -> bool:
        return os.path.exists(self.local_file)

    def download_file(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            with open(self.local_file, "wb") as f:
                f.write(response.content)
            print(f"⬇️ Downloaded file to: {self.local_file}")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to download file: {e}")

    def move_old_files_to_archive(self):
        for fname in os.listdir(self.base_dir):
            if fname.startswith("instrument_") and fname.endswith(".csv") and fname != self.filename:
                try:
                    date_str = fname.replace("instrument_", "").replace(".csv", "")
                    file_date = datetime.strptime(date_str, "%Y_%m_%d").date()
                    if file_date < self.today:
                        src = os.path.join(self.base_dir, fname)
                        dst = os.path.join(self.archive_dir, fname)
                        shutil.move(src, dst)
                        print(f"📦 Archived: {fname}")
                except Exception as e:
                    print(f"⚠️ Skipped {fname} due to error: {e}")

    def delete_old_archives(self):
        cutoff_date = self.today - timedelta(days=30)
        for fname in os.listdir(self.archive_dir):
            if fname.startswith("instrument_") and fname.endswith(".csv"):
                try:
                    date_str = fname.replace("instrument_", "").replace(".csv", "")
                    file_date = datetime.strptime(date_str, "%Y_%m_%d").date()
                    if file_date < cutoff_date:
                        os.remove(os.path.join(self.archive_dir, fname))
                        print(f"🗑️ Deleted archive file: {fname}")
                except Exception as e:
                    print(f"⚠️ Could not delete {fname}: {e}")

    def load_file(self):
        if not self.already_downloaded_today():
            self.download_file()
        else:
            print("⏭️ Today's file already exists. Skipping download.")

        try:
            df = pd.read_csv(self.local_file, low_memory=False)

            df.rename(columns={
                "SEM_EXM_EXCH_ID": "sem_exm_exch_id",
                "SEM_SEGMENT": "sem_segment",
                "SEM_SMST_SECURITY_ID": "sem_smst_security_id",
                "SEM_INSTRUMENT_NAME": "sem_instrument_name",
                "SEM_EXPIRY_CODE": "sem_expiry_code",
                "SEM_TRADING_SYMBOL": "sem_trading_symbol",
                "SEM_LOT_UNITS": "sem_lot_units",
                "SEM_CUSTOM_SYMBOL": "sem_custom_symbol",
                "SEM_EXPIRY_DATE": "sem_expiry_date",
                "SEM_STRIKE_PRICE": "sem_strike_price",
                "SEM_OPTION_TYPE": "sem_option_type",
                "SEM_TICK_SIZE": "sem_tick_size",
                "SEM_EXPIRY_FLAG": "sem_expiry_flag",
                "SEM_EXCH_INSTRUMENT_TYPE": "sem_exch_instrument_type",
                "SEM_SERIES": "sem_series",
                "SM_SYMBOL_NAME": "sm_symbol_name"
            }, inplace=True)

            df.dropna(subset=["sem_smst_security_id"], inplace=True)

            # Replace all NaT/NaN/pd.NA with None
            df = df.replace({pd.NA: None, pd.NaT: None, float('nan'): None})

            # Convert all fields to string for simplified loading
            df = df.astype(str)
            df = df.replace({'nan': None, 'NaT': None, 'None': None})

            df["created_at"] = datetime.utcnow()

            records = df.to_dict(orient="records")

            with get_db_session() as session:
                session.execute(text("TRUNCATE TABLE all_instruments_list RESTART IDENTITY"))
                session.bulk_insert_mappings(AllInstrumentsList, records)
                print(f"✅ Loaded {len(records)} records into all_instruments_list")

            send_telegram_message(
                f"✅ Instrument data updated in PostgreSQL\n"
                f"📅 Date: {self.today.strftime('%Y-%m-%d')}\n"
                f"📄 Records inserted: {len(records)}\n"
                f"📁 File: {self.filename}",
                parse_mode=None
            )

            self.move_old_files_to_archive()
            self.delete_old_archives()

        except SQLAlchemyError as e:
            error_msg = f"❌ Database error while loading instrument file\n🔍 Error: {e}"
            print(error_msg)
            send_telegram_message(error_msg[:4000], parse_mode=None)

        except FileNotFoundError:
            error_msg = f"❌ File not found: {self.local_file}"
            print(error_msg)
            send_telegram_message(error_msg, parse_mode=None)

        except Exception as e:
            error_msg = f"❌ Unexpected error during instrument load\n🔍 Error: {e}"
            print(error_msg)
            send_telegram_message(error_msg[:4000], parse_mode=None)
