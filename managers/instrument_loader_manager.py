from services.instrument_loader_service import InstrumentLoaderService
from utils.telegram_notifier import send_telegram_message
from datetime import datetime


class InstrumentLoaderManager:
    """
    Manager class to control loading of all_instruments_list and manage alerts.
    """
    def __init__(self):
        self.loader = InstrumentLoaderService()

    def refresh_instrument_file_and_load(self):
        try:
            self.loader.load_file()
            return True
        except Exception as e:
            error_msg = (
                f"❌ Failed to load all instruments\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"🔍 Error: {e}"
            )
            print(error_msg)
            send_telegram_message(error_msg, parse_mode=None)
            return False
