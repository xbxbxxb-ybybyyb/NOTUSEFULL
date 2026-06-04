"""实盘策略（Albest, Everest, Kunlun_mix, Kunlun_pure）回测跟踪程序（新增l2p跟踪），按组合和市场区分的结果——update @2021.10.31"""

import datetime
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams
from DataAPI.TradingDay import trading_day_gap
from SP.SP_Params import print_strategy_lib
from SP.UtilsSP.CollectLiveParams import CollectLiveParams, EVEREST_DST_PATH
from SP.track_sp_l2p import stock_sp_config, kunlun_sp_voting_config
from SP.TrackSP.track_sp_daily import TrackDiffParams
from SP.TrackSP.track_sp_index_daily import triggers, get_config_albest, get_config_everest, get_config_sp_all


mode = 'spark'  # local, spark, ray


def main():
    # bt_date = '20220606'
    bt_date = trading_day_gap(datetime.datetime.now().strftime("%Y%m%d"), -1)
    triggers(bt_date, mode='spark')
    # start_bt(bt_date)


def start_bt(bt_date):
    strategy_params = StrategyParams(mode)
    track_sp(strategy_params, bt_date)
    track_params(strategy_params, bt_date, mode)
    track_index(strategy_params, bt_date)
    strategy_params.check_sp_existing_code(bt_date)

    sp_track = RunBT(strategy_params.strategy_params, mode)
    # sp_track.start_bt()
    sp_track.analyze_result(is_transfer_file=False, is_classify_res=False, multiprocess_nums=20)


def track_sp(strategy_params, bt_date):
    CollectLiveParams('Everest', bt_date, bt_date, True, EVEREST_DST_PATH).run()
    print_strategy_lib(bt_date)
    stock_sp_config('Albest', bt_date, strategy_params, bt_mode='all')
    stock_sp_config('Everest1S', bt_date, strategy_params, bt_mode='all')
    kunlun_sp_voting_config('Kunlun_mix', bt_date, strategy_params, bt_mode='all')
    kunlun_sp_voting_config('Kunlun_pure', bt_date, strategy_params, bt_mode='all')


def track_params(strategy_params, bt_date, mode):
    tp = TrackDiffParams(bt_date, mode)
    tp.stock_pro_bt(strategy_params, bt_date)
    tp.track_stock_diff_mv(strategy_params, bt_date)
    tp.track_stock_diff_oc(strategy_params, bt_date)
    tp.track_stock_diff_open_time(strategy_params, bt_date)
    tp.cb_pro_bt(strategy_params, bt_date)
    tp.track_kunlun_diff_size(strategy_params, bt_date)
    tp.track_kunlun_diff_open_time(strategy_params, bt_date)
    tp.track_kunlun_diff_liquidity_ratio(strategy_params, bt_date)
    tp.track_kunlun_mix_voting(strategy_params, bt_date)


def track_index(strategy_params, bt_date):
    get_config_sp_all(strategy_params, bt_date)
    get_config_albest(strategy_params, bt_date)
    get_config_everest(strategy_params, bt_date)


if __name__ == '__main__':
    main()
