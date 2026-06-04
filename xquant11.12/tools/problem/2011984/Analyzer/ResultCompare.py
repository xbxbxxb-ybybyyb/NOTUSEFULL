"""两组bt结果对比"""

import pandas as pd
from DataAPI.DataView import load_pickle_file


def main():
    st_date, ed_date = '20220315', '20220520'
    size = 1
    signal_lib = 'Albest20211101Order1Signals'
    abs_path_bt = f'/data/user/011668/bt_test/Everest1S/bt-{st_date}-{ed_date}/'
    abs_path_list = [
        f'{abs_path_bt}/1800-ExecutorAlbestSP1S-Albest20211101Order1Signals-dy{size}_oc0.3',
        f'{abs_path_bt}/1800-ExecutorAlbestSP1SVolRatio-{signal_lib}-dy{size}_oc0.3_vol_ratio'
    ]
    tags = ['origin', 'vol_ratio']
    result_compare(abs_path_list)


def result_compare(abs_path_list):
    order1 = load_pickle_file(f'{abs_path_list[0]}/CombineData/orders.pickle')
    order2 = load_pickle_file(f'{abs_path_list[1]}/CombineData/orders.pickle')
    big_gap_df = code_date_gap(abs_path_list)
    for (date, code) in big_gap_df.index:
        order1_code = order1[(order1['code'] == code) & (order1['date'] == date.replace('-', ''))]
        order2_code = order2[(order2['code'] == code) & (order2['date'] == date.replace('-', ''))]
        print('')


def code_date_gap(abs_path_list):
    res_list = []
    for abs_path in abs_path_list:
        data = pd.read_excel(f'{abs_path}/daily_split.xlsx', index_col=0).stack()
        res_list.append(data)
    res_df = pd.concat(res_list, axis=1)
    res_df['gap'] = (res_df[0] - res_df[1]).abs()
    res_df = res_df.sort_values(by='gap', ascending=False)
    return res_df


if __name__ == '__main__':
    main()
