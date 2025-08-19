from managers.instrument_loader_manager import InstrumentLoaderManager
from managers.instrument_master_loader_manager import InstrumentMasterLoaderManager


def main():
    print("🚀 Starting full instrument refresh process...")

    # Step 1: Load instrument file and insert into all_instruments_list
    instrument_loader = InstrumentLoaderManager()
    file_path = instrument_loader.refresh_instrument_file_and_load()

    # Step 2: Populate instrument_master if file was loaded successfully
    if file_path:
        master_loader = InstrumentMasterLoaderManager()
        master_loader.refresh_instruments()
    else:
        print("⚠️ Skipping instrument_master update due to failure in loading file.")


if __name__ == "__main__":
    main()
