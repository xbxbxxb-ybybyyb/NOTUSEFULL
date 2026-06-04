from typing import List
import pandas as pd


def get_data_from_csv(symbol: str, signal_csv_dir: str, dates: List[str]) -> pd.DataFrame:
    # symbol = symbol[: 6]
    file_paths = []
    for date in dates:
        file_path = signal_csv_dir + '/' + symbol + '_' + date + '.csv'
        file_paths.append(file_path)
    data = None
    for file_path in file_paths:
        data_single = pd.read_csv(file_path)
        if data is not None:
            data = pd.concat([data, data_single], axis=0)  # concat vertically
        else:
            data = data_single
    return data


