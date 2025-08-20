# run_ledger_sync.py

from managers.ledger_manager import LedgerManager

if __name__ == "__main__":
    print("🚀 Starting Ledger Report Sync...")

    # Set full_backfill=True for first time; False for daily incremental sync
    full_backfill = False

    manager = LedgerManager()
    manager.run_incremental(full_backfill=full_backfill)

    print("✅ Ledger sync completed.")
