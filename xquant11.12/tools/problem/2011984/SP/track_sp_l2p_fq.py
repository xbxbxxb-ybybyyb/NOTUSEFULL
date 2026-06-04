"""实盘策略（Albest, Everest, Kunlun_mix, Kunlun_pure）回测跟踪程序（新增l2p跟踪），按组合和市场区分的结果——update @2021.10.31"""

import datetime
import pandas as pd
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from xquant.factordata import FactorData
from DataAPI.TradingDay import trading_day_gap
from DataAPI.DataView import file_exist
from Utils.LinkMessage import LinkMessage


fa = FactorData()
mode = 'spark'


def main():
    # bt_date = '20220728'
    if datetime.datetime.now().hour < 15:  # 15点以前跑当天
        bt_date = datetime.datetime.now().strftime("%Y%m%d")
    else:  # 15点以后跑明天
        bt_date = trading_day_gap(datetime.datetime.now().strftime("%Y%m%d"), 1)
    st_date, ed_date = trading_day_gap(bt_date, -41), trading_day_gap(bt_date, -1)

    if not check(bt_date, st_date, ed_date):
        code_list, vol_list = get_code_dict(trading_day_gap(bt_date, -1))
        code_vol_dict = dict(zip(code_list, vol_list))
        # signal_lib_albest = 'ray_albest_20211101_20211116_order'
        signal_lib_everest = 'Albest20211101Order1Signals'
        suffix = f'_fq_{st_date}_{ed_date}'

        # triggers_albest(code_list, st_date, ed_date, signal_lib_albest, suffix)
        triggers_everest(code_list, st_date, ed_date, signal_lib_everest, suffix)

        strategy_params = StrategyParams(mode, bt_type='sp')
        # get_config_albest(strategy_params, code_vol_dict, st_date, ed_date, signal_lib_albest, suffix)
        get_config_everest(strategy_params, code_vol_dict, st_date, ed_date, signal_lib_everest, suffix)
        sp_track = RunBT(strategy_params.strategy_params, mode, bt_type='sp')
        sp_track.start_bt()
        sp_track.analyze_result(is_transfer_file=False, is_classify_res=True, multiprocess_nums=1)

        if check(bt_date, st_date, ed_date):
            text_link = f'【{bt_date}实盘】Everest分券bt结果完成，{st_date}-{ed_date}，合计{len(code_vol_dict)}只标的'
            LinkMessage().sendMessage("011668", text_link)
            LinkMessage().sendMessage("015629", text_link)
        else:
            LinkMessage().sendMessage("011668", f'【{bt_date}实盘】Everest分券bt结果失败，请检查')


def check(bt_date, st_date, ed_date):
    abs_path = f'/data/user/011668/bt_test/EverestFQ/bt-{st_date}-{ed_date}/' \
        f'test-ExecutorAlbestSP1SIntra-Albest20211101Order1Signals-dy_fq_{st_date}_{ed_date}/TotalSummary.xls'
    if file_exist(abs_path):
        data = pd.read_excel(abs_path, index_col=0)
        if data.shape[0] > 0 and data['afterCostProfit'].sum() > 0:
            return True
    return False


def triggers_albest(code_list, st_date, ed_date, signal_lib, suffix):
    from BT.Dy_Triggers.SignalCVIntra import Task

    save_path = f'/data/user/011668/CVTriggers/Albest/{signal_lib}{suffix}'
    Task(code_list, st_date, ed_date, 'Albest', signal_lib, save_path, time_list=['10:00:00']).start(mode=mode)  # local, multi_processing, spark


def triggers_everest(code_list, st_date, ed_date, signal_lib, suffix):
    from BT.Dy_Triggers.SignalCVIntra import Task
    mock_lib = 'Channel1STickDataLib'
    save_path = f'/data/user/011668/CVTriggers/Albest/{signal_lib}{suffix}'
    Task(code_list, st_date, ed_date, 'Albest', signal_lib, save_path, time_list=['10:00:00'],
         tag_lib=signal_lib, mock_lib=mock_lib, is_add_mock=False, overwrite_params={'min_triggers': 15}).start(mode=mode)  # local, multi_processing, spark


def get_code_dict(today):
    tomorrow = fa.tradingday(today, 2)[-1]
    portfolio = pd.read_excel("/data/user/011477/order/T0/T0_CV_Split/{}/{}_easy.xlsx".format(tomorrow, tomorrow))
    common_stock_list = [code for code in sorted(set(portfolio["证券代码"].tolist())) if code.endswith(".SZ")]
    portfolio = portfolio[portfolio["证券代码"].isin(common_stock_list)]
    codes = portfolio["证券代码"].tolist()
    volumes = portfolio["证券额度"].tolist()
    return codes, volumes


def get_config_albest(strategy_params, code_vol_dict, st_date, ed_date, signal_lib, suffix):
    overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, 'Albest', suffix=suffix)
    params_dynamic = {
        'st_date': st_date,
        'ed_date': ed_date,
        'strategy': 'Albest',
        'portfolio': 'test',
        'code_vol_dict': code_vol_dict,
        'executor_str': 'Executor.ExecutorAlbestSPIntra',  # ExecutorAlbestSP, ExecutorAlbestSPIntra
        'signal_lib': signal_lib,
        'out_dir': f'bt_test/EverestFQ',
        'overwrite_params': {'order_capacity_ratio': 0.3},
        'overwrite_params_by_code': overwrite_params_by_code,
        'suffix_name': f'-dy{suffix}',
    }
    strategy_params.add_params(params_dynamic)


def get_config_everest(strategy_params, code_vol_dict, st_date, ed_date, signal_lib, suffix):
    overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, 'Albest', suffix=suffix)
    params_dynamic = {
        'st_date': st_date,
        'ed_date': ed_date,
        'strategy': 'Albest',
        'portfolio': 'test',
        'freq': '1s',
        'code_vol_dict': code_vol_dict,
        'executor_str': f'Executor.ExecutorAlbestSP1SIntra',
        'signal_lib': signal_lib,
        'out_dir': f'bt_test/EverestFQ',
        'overwrite_params': {'time_list': ['09:30:00', '10:00:00'], 'order_capacity_ratio': 0.3},
        'overwrite_params_by_code': overwrite_params_by_code,
        'suffix_name': f'-dy{suffix}',
    }
    strategy_params.add_params(params_dynamic)


if __name__ == '__main__':
    main()
