"""SignalCV运行的main函数————update @2021.8.3"""

from DataAPI.GetCodeVol import get_cb_code, get_index_code, get_all_code
import pandas as pd


def main():
    main_stock()


def main_stock():
    from BT.Dy_VolRatio.RatioVol import Task
    suffix = ''
    code_list = []
    st_date, ed_date = '20220315', '20220520'
    strategy = 'Albest'
    signal_lib = 'Albest20211101Order1Signals'
    save_path = f'/data/user/011668/DyVolRatio/{strategy}/{signal_lib}{suffix}'
    Task(code_list, st_date, ed_date, strategy, signal_lib, save_path, is_add_mock=False).start(mode='spark')  # local, multi_processing, spark


if __name__ == '__main__':
    main()
