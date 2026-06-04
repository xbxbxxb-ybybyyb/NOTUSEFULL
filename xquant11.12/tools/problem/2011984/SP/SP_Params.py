import datetime
import pandas as pd
from DataAPI.TradingDay import trading_day
from Utils.UtilsTime import date_t


def get_sp_lib(trade_date, strategy, type='res'):
    if strategy == 'Albest':
        return get_res_lib_albest(trade_date, type)

    elif strategy == 'Everest':
        return get_res_lib_everest(trade_date, type)

    elif strategy == 'Everest1S':
        return get_res_lib_everest_1s(trade_date, type)

    elif strategy == 'Kunlun_mix':
        return get_res_lib_kunlun_mix(trade_date, type)

    elif strategy == 'Kunlun_pure':
        return get_res_lib_kunlun_pure(trade_date, type)


def get_lib_range(strategy, type, lib_name):
    # 信号库使用的日期
    if 'pro' in type:
        return [None, None]
    use_date = []
    now_date = datetime.datetime.now().strftime("%Y%m%d")
    for date in trading_day('20210801', now_date):
        if get_sp_lib(date, strategy, type) == lib_name:
            use_date.append(date)
    if len(use_date) > 0:
        return [date_t(use_date[0]), date_t(use_date[-1])]
    else:
        raise ValueError('信号库没有交易过')


def print_strategy_lib(trade_date=None):
    if trade_date is None:
        trade_date = datetime.datetime.now().strftime("%Y%m%d")
    for strategy in ['Albest', 'Everest', 'Kunlun_mix', 'Kunlun_pure']:
        lib_pro = get_sp_lib(trade_date, strategy, 'pro')
        lib_res = get_sp_lib(trade_date, strategy, 'res')
        strategy_str = strategy + ': ' + ' ' * (12 - len(strategy))
        lib_pro_str = lib_pro + ' ' * (35 - len(lib_pro))
        print(f'{strategy_str} {lib_pro_str} {lib_res}')
    print('-' * 100)


def get_strategy_lib_df(trade_date, strategy_list):
    lib_df = []
    for t in ['pro', 'res']:
        for strategy in ['Albest', 'Everest', 'Kunlun_mix', 'Kunlun_pure']:
            if strategy in strategy_list:
                if t == 'res' and strategy == 'Albest':
                    lib_sh = get_sp_lib(trade_date, strategy, 'res_sh')
                    first_trade_date = get_lib_range(strategy, 'res_sh', lib_sh)[0]
                    lib_df.append([strategy, 'res_sh', lib_sh, first_trade_date])
                    lib_sz = get_sp_lib(trade_date, strategy, 'res_sz')
                    first_trade_date = get_lib_range(strategy, 'res_sz', lib_sz)[0]
                    lib_df.append([strategy, 'res_sz', lib_sz, first_trade_date])
                else:
                    lib_ = get_sp_lib(trade_date, strategy, t)
                    first_trade_date = get_lib_range(strategy, t, lib_)[0]
                    lib_df.append([strategy, t, lib_, first_trade_date])
    lib_df = pd.DataFrame(lib_df, columns=['策略', '类型', '信号库', '上线日期'])
    return lib_df


def get_res_lib_albest(trade_date, type):
    if type == 'pro':
        if trade_date >= '20211108':
            return 'AlbestProductionSignals_20211025'
    elif type == 'res_sh':
        if trade_date >= '20211228':
            return 'ray_albest_20211101_20211116'
        elif trade_date >= '20211215':
            return 'ray_albest_20210701_20210912'
    elif type == 'res_sz':
        if trade_date >= '20220111':
            return 'ray_albest_20211101_20211116_order'
        elif trade_date >= '20211215':
            return 'ray_albest_20210701_20210928_order'
    elif type == 'res':
        return {'sh': get_res_lib_albest(trade_date, 'res_sh'), 'sz': get_res_lib_albest(trade_date, 'res_sz')}


def get_res_lib_everest(trade_date, type):
    if type == 'pro':
        if trade_date >= '20210826':
            return 'EverestProductionSignals'
    elif type in ['res', 'res_sh', 'res_sz']:
        if trade_date >= '20211223':
            return 'Everest20211001_20210515'
        elif trade_date >= '20210827':
            return 'Everest20210201_20210515'
        elif trade_date >= '20210329':
            return 'BigEasy20210201'


def get_res_lib_everest_1s(trade_date, type):
    if type == 'pro':
        if trade_date >= '20220419':
            return 'EverestProductionSignals'
    elif type in ['res', 'res_sh', 'res_sz']:
        if trade_date >= '20220505':
            return 'Albest20211101Order1Signals'
        elif trade_date >= '20220419':
            return 'Albest202111011Signals'


def get_res_lib_kunlun_mix(trade_date, type):
    if type == 'pro':
        return 'WuKongProductionSignals'
    elif type == 'res':
        if trade_date >= '20220415':
            return 'ray_cb_stock_20220201_20210506_sync'
        elif trade_date >= '20211219':
            return 'ray_cb_stock_20211001_20210506_sync'
        elif trade_date >= '20210830':
            return 'ray_cb_stock_20210501_20210506_sync'
        elif trade_date >= '20210301':
            return 'ray_cb_stock_20210201_20210506'
    elif type in ['res_sh', 'res_sz', 'res_cyb']:
        return get_res_lib_kunlun_mix(trade_date, 'res')


def get_res_lib_kunlun_pure(trade_date, type):
    if type == 'pro':
        return 'WuKongProductionSignals2'
    elif type == 'res':
        if trade_date >= '20210830':
            return 'ray_cb_20210201_20210506_pure'
