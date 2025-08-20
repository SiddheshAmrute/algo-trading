# run_trade_history_sync.py

from managers.trade_history_manager import TradeHistoryManager

if __name__ == "__main__":
    print("🚀 Starting Trade History Sync...")

    # Set full_backfill=True for first time; False for daily incremental sync
    full_backfill = False

    manager = TradeHistoryManager()
    manager.run_incremental(full_backfill=full_backfill)

    print("✅ Trade history sync completed.")
