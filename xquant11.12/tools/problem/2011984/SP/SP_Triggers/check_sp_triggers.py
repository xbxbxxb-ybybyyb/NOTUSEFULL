import os
import json
import pandas as pd
import numpy as np
import datetime
from Utils.LinkMessage import LinkMessage
from xquant.xqutils.xqfile import HDFSFile
from xquant.factordata import FactorData


trade_date = datetime.datetime.now().strftime("%Y%m%d")
user_id = '011668'
lm = LinkMessage()


def main():
    check_albest()
    check_everest()
    check_kunlun()


def check_albest():
    is_send = True
    print('Start Check Albest'.center(100, '*'))
    code_select = pd.read_excel(f'/data/user/011477/order/T0/T0_CV_Split/{trade_date}/{trade_date}_easy.xlsx')['证券代码'].to_list()
    code_select = list(sorted(set(code_select)))

    code_select_sh = [x for x in code_select if x.endswith('.SH')]
    signal_lib_sh = 'ray_albest_20220201_20220414_new'
    save_path_sh = f'/data/user/{user_id}/CVTriggers/SPTriggers/Albest/{trade_date}/{signal_lib_sh}'
    code_non_existing_sh = list(sorted(set(code_select_sh) - set([x[:-5] for x in file_list_dir(save_path_sh)])))
    if len(code_non_existing_sh) == 0:
        print(f'【Albest SH】 √ : {len(code_select_sh)}')
        check_triggers('Albest', save_path_sh)
    else:
        is_send = False
        print(f'【Albest SH】 × : Total {len(code_select_sh)}, Loss {len(code_non_existing_sh)}')

    code_select_sz = [x for x in code_select if x.endswith('.SZ')]
    signal_lib_sz = 'ray_albest_20211101_20211116_order'
    save_path_sz = f'/data/user/{user_id}/CVTriggers/SPTriggers/Albest/{trade_date}/{signal_lib_sz}'
    code_non_existing_sz = list(sorted(set(code_select_sz) - set([x[:-5] for x in file_list_dir(save_path_sz)])))
    if len(code_non_existing_sh) == 0:
        print(f'【Albest SZ】 √ : {len(code_select_sz)}')
        check_triggers('Albest', save_path_sz)
    else:
        is_send = False
        print(f'【Albest SZ】 × : Total {len(code_select_sz)}, Loss {len(code_non_existing_sz)}')

    if is_send:
        lm.sendMessage(user_id, f'{user_id} {trade_date} Albest实盘阈值已生成：{len(code_select_sh)}只上海标的+{len(code_select_sz)}只深圳标的')
        lm.sendMessage('017023', f'{user_id} {trade_date} Albest实盘阈值已生成：{len(code_select_sh)}只上海标的+{len(code_select_sz)}只深圳标的')


def check_everest():
    is_send = True
    print('Start Check Everest'.center(100, '*'))
    code_select = get_everest_live_params_stock_list(trade_date)
    freq = "1"
    signal_lib = 'Albest20220201Order{}Signals'.format(freq)
    save_path = f'/data/user/{user_id}/CVTriggers/SPTriggers/Everest1S/{trade_date}/{signal_lib}'
    code_non_existing = list(sorted(set(code_select) - set([x[:-5] for x in file_list_dir(save_path)])))
    if len(code_non_existing) == 0:
        print(f'【Everest】 √ : {len(code_select)}')
        check_triggers('Everest', save_path)
    else:
        is_send = False
        print(f'【Everest】 × : Total {len(code_select)}, Loss {len(code_non_existing)}')

    if is_send:
        lm.sendMessage(user_id, f'{user_id} {trade_date} Everest实盘阈值已生成：{len(code_select)}只标的')
        lm.sendMessage('015629', f'{user_id} {trade_date} Everest实盘阈值已生成：{len(code_select)}只标的')


def check_kunlun():
    is_send = True
    print('Start Check Kunlun'.center(100, '*'))
    code_select = get_cb_code(FactorData().tradingday(trade_date, -60)[0], trade_date)
    signal_lib = 'ray_cb_stock_20220201_20210506_sync'
    save_path = f'/data/user/{user_id}/CVTriggers/SPTriggers/Kunlun/{trade_date}/{signal_lib}'
    code_non_existing = list(sorted(set(code_select) - set([x[:-5] for x in file_list_dir(save_path)])))
    if len(code_non_existing) == 0:
        print(f'【Kunlun】 √ : {len(code_select)}')
        check_triggers('Kunlun', save_path)
    else:
        is_send = False
        print(f'【Kunlun】 × : Total {len(code_select)}, Loss {len(code_non_existing)}')

    if is_send:
        lm.sendMessage(user_id, f'{user_id} {trade_date} Kunlun实盘阈值已生成：{len(code_select)}只标的')
        lm.sendMessage('015390', f'{user_id} {trade_date} Kunlun实盘阈值已生成：{len(code_select)}只标的')


def check_triggers(strategy, trigger_path):
    all_file = file_list_dir(trigger_path)
    if strategy == 'Albest' or strategy == 'Everest':
        count1, count2 = [], []
        for f in all_file:
            trigger_code = load_json_file(f'{trigger_path}/{f}')
            if np.abs(trigger_code[f'{trade_date}_09:30:00']['longTriggerRatio']) > 100:
                count1.append(f[:-5])
            if np.abs(trigger_code[f'{trade_date}_10:00:00']['longTriggerRatio']) > 100:
                count2.append(f[:-5])
        if len(count1) > 0:
            print(f'{strategy} 09:30:00 Invalid 99999: {count1}')
        if len(count2) > 0:
            print(f'{strategy} 10:00:00 Invalid 99999: {count2}')
    elif strategy == 'Kunlun':
        count = []
        for f in all_file:
            trigger_code = load_json_file(f'{trigger_path}/{f}')
            if np.abs(pd.DataFrame(trigger_code[trade_date]).sum(axis=1)['longTriggerRatio']) > 100:
                count.append(f[:-5])
        if len(count) > 0:
            print(f'Kunlun Invalid 99999: {count}')


def file_list_dir(file_dir, dfs=None):
    if file_dir.startswith('/data/user/'):  # NFS
        return os.listdir(file_dir)
    else:  # HDFS
        py = HDFSFile(dfs)
        return py.listdir(file_dir)


def load_json_file(file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'r') as f:
            data = json.load(f)
    else:
        py = HDFSFile(dfs)
        with py.open(file_name, 'rb') as f:  # HDFS
            data = json.load(f)
    return data


def get_everest_live_params_stock_list(date):
    db_stock_list = pd.read_csv("/data/user/015629/LiveChannel1sTick/LiveStockList/{}/{}.csv".format(date, date))["stock"].tolist()
    code_list = [c for c in db_stock_list if c.endswith(".SZ")]
    return code_list


def get_cb_code(st_date, ed_date, gap=5):
    """获取转债样本"""
    code_list = []
    for i, trade_date in enumerate(FactorData().tradingday(int(st_date), int(ed_date))[::-1]):
        trade_file = "/data/user/666888/WuKong/portfolios/WuKong_{}.xlsx".format(trade_date)
        if i % gap == 0 and os.path.exists(trade_file):
            df = pd.read_excel(trade_file)
            code_list += list(df['证券代码'])
    codes = list(sorted(set(code_list)))
    return codes


if __name__ == '__main__':
    main()
