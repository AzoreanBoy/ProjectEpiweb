import pandas as pd
import psutil
import traceback
from epilab.binfile import bin_file


def process_files(files: list[bin_file], window: int = 5) -> list[pd.DataFrame]:
    """
    Process all bin files
    :param files: list of bin files
    :return: list of dataframes
    """
    if not files:
        return []

    def get_system_memory_usage() -> float:
        return psutil.virtual_memory().percent

    print(f"Processing file {files[0].filename}")
    data = files[0].read_data_file()

    for file_index in range(1, len(files)):
        print(f"Processing file {files[file_index].filename}")

        time_diff = files[file_index].startTs - files[file_index - 1].stopTs
        if time_diff < pd.Timedelta(seconds=window):
            try:
                data = pd.concat([data, files[file_index].read_data_file()], axis=0)
            except:
                print(f"Error in file {files[file_index].filename}")
        else:
            yield data
            data = files[file_index].read_data_file()

    if not data.empty:
        yield data
