import requests
from utils.db_session import get_db_session
from utils.telegram_notifier import send_telegram_message
from api.data_api import DhanDataAPI
from db.init_db import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


class PreMarketHealthCheck:
    """
    Health Check service to verify critical systems before starting the Algo Trading Engine.
    """

    def __init__(self):
        self.dhan_api = DhanDataAPI()

    def check_internet(self) -> bool:
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def check_database(self) -> bool:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError:
            return False

    def check_dhan_api(self) -> bool:
        try:
            test_symbol = "RELIANCE"  # Use a safe and active equity symbol
            ltp = self.dhan_api.get_ltp_for_instruments([test_symbol])
            return bool(ltp)
        except Exception:
            return False

    def check_telegram(self) -> bool:
        try:
            send_telegram_message("✅ Pre-market Health Check Test Message")
            return True
        except Exception:
            return False

    def run_health_check(self) -> bool:
        """
        Run all health checks and return overall status.
        """
        print("\n🩺 Running Pre-Market Health Checks...")

        internet_ok = self.check_internet()
        database_ok = self.check_database()
        dhan_api_ok = self.check_dhan_api()
        telegram_ok = self.check_telegram()

        all_ok = internet_ok and database_ok and dhan_api_ok and telegram_ok

        print("───────────────────────────────────────")
        print(f"🌐 Internet Connection: {'✅' if internet_ok else '❌'}")
        print(f"🗄️ Database Connection: {'✅' if database_ok else '❌'}")
        print(f"🏦 Dhan API Access: {'✅' if dhan_api_ok else '❌'}")
        print(f"🔔 Telegram Alerts: {'✅' if telegram_ok else '❌'}")
        print("───────────────────────────────────────")

        if all_ok:
            print("\n✅ Health check passed!")
            send_telegram_message("✅ Health check passed.")
        else:
            print("\n🚨 Health Check Failed! Fix issues before starting Algo!")
            send_telegram_message("🚨 Health Check Failed! Fix issues before launch.")

        return all_ok


if __name__ == "__main__":
    checker = PreMarketHealthCheck()
    checker.run_health_check()