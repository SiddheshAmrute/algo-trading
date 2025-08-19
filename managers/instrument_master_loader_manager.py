from services.instrument_master_loader_service import InstrumentMasterLoaderService
from utils.telegram_notifier import send_telegram_message
from datetime import datetime


class InstrumentMasterLoaderManager:
    """
    Manager class to control instrument_master population and send Telegram alerts.
    """

    def __init__(self):
        self.loader = InstrumentMasterLoaderService()

    def refresh_instruments(self):
        try:
            count = self.loader.load_instrument_master()
            message = (
                f"✅ Instrument master updated successfully\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"📄 Records inserted: {count}"
            )
            send_telegram_message(message)
        except Exception as e:
            error_msg = (
                f"❌ Failed to update instrument master\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"🔍 Error: {e}"
            )
            print(error_msg)
            send_telegram_message(error_msg, parse_mode=None)
