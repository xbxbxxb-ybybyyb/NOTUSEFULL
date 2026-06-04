""" update@ 2021.3.2
获取股票代码和对应的成交量，包括2部分：
（1）实盘交易的时候，对应的股票代码和量
（2）对应的指数成分股，对应的股票代码和量
"""

import os
import numpy as np
import pandas as pd
from DataAPI.TradingDay import trading_day, trading_day_gap
from DataAPI.DataTools import get_stock_daily_result
from DataAPI.DataToolsCbond import cbond_set
from DataAPI.DataView import load_json_file, file_exist
from xquant.factordata import FactorData


index_base_date = 20210331
fa = FactorData()


class GetCodeVol:
    def __init__(self, st_date, ed_date, code=None, market='all'):
        self.st_date = st_date
        self.ed_date = ed_date
        self.code_filter = code
        self.market = market

    def get_index_code(self, portfolio, base_date, index_size):
        """股票指数成分股，portfolio为：hs300, zz500, 800"""
        codes, volumes = get_index_code_volume(portfolio, base_date, index_size)
        return self.__out(codes, volumes)

    def get_cyb_code(self, base_date, n=60, code_size=500 * 1e4):
        """创业板股票代码"""
        codes = get_cyb_code(base_date, n=n)
        close = get_stock_daily_result(codes, [str(base_date)], ['close']).droplevel(0)['close']
        volumes = [code_size / close[x] for x in codes]
        volumes = [int(x) if ~np.isnan(x) else 0 for x in volumes]
        return self.__out(codes, volumes)

    def get_kcb_code(self, base_date, n=60):
        """科创板股票代码"""
        codes = get_kcb_code(base_date, n=n)
        volumes = [1e10] * len(codes)
        return self.__out(codes, volumes)

    def get_cb_code(self):
        res_list = []
        for i, trade_date in enumerate(trading_day(int(self.st_date), int(self.ed_date))):
            trade_file = "/data/user/666888/WuKong/portfolios/WuKong_{}.xlsx".format(trade_date)
            if i % 5 == 0 and os.path.exists(trade_file):
                df = pd.read_excel(trade_file)
                res_list.append(df.iloc[:, [0, 3]])
        res = pd.concat(res_list, axis=0).groupby("证券代码").max()
        codes = list(res.index)
        volumes = [int(x) for x in res.values]
        return self.__out(codes, volumes)

    def get_sp_code(self, portfolio, sub_portfolio=''):
        if self.st_date != self.ed_date:
            raise ValueError("实盘回测只能测一天，start_date应该等于end_date")
        if portfolio.startswith('Albest_sp') or portfolio.startswith('Everest_sp') or portfolio.startswith('Everest1S_sp'):
            strategy = portfolio.split('_')[0]
            if strategy == 'Albest':
                # param_path = f'/data/user/666888/Algo/portfolios_sp/{self.st_date}/'
                date = self.st_date
                root_path = "/data/user/011477/Trade_Docs/{}/".format(date)
                date_paths = [os.path.join(root_path, path) for path in os.listdir(root_path) if "Algo_{}".format(date) in path]
                code_dict = {}
                for date_path in date_paths:
                    portfolio_files = [f for f in os.listdir(date_path) if f.endswith(".xlsx") and date in f]
                    for portfolio_file in portfolio_files:
                        portfolio_path = os.path.join(date_path, portfolio_file)
                        portfolio = pd.read_excel(portfolio_path)
                        portfolio = portfolio.reset_index().set_index('证券代码')
                        portfolio_codes = portfolio["证券额度"].to_dict()
                        for code, number in portfolio_codes.items():
                            if code not in code_dict.keys():
                                code_dict[code] = number
                            else:
                                code_dict[code] += number
                codes = list(code_dict.keys())
                volumes = list(code_dict.values())
            else:  # Everest
                if self.st_date < '20211111':
                    param_path = f'/data/user/015629/Easy/productionParams/Easy_{self.st_date}'
                else:
                    param_path = f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{self.st_date}'

                all_file = os.listdir(param_path)
                res_list = []
                for file in all_file:
                    if (strategy == 'Albest' and file.endswith('_sp.xlsx')) or \
                            (strategy.startswith('Everest') and file.startswith('easy_') and file.endswith(f'_{self.st_date}.xlsx')):
                        res_list.append(pd.read_excel(f'{param_path}/{file}'))
                portfolio_df = pd.concat(res_list)
                if sub_portfolio != '':
                    if isinstance(sub_portfolio, list):
                        portfolio_df = portfolio_df.set_index('买入交易账户').loc[[int(x) for x in sub_portfolio]].reset_index()
                    else:
                        portfolio_df = portfolio_df[portfolio_df['买入交易账户'] == int(sub_portfolio)]
                res_df = portfolio_df[['证券代码', '证券额度']].groupby('证券代码').sum()
                codes = list(res_df.index)
                volumes = list(res_df['证券额度'])
        elif portfolio.startswith('Kunlun_sp'):
            if portfolio == 'Kunlun_sp_mix':
                if self.st_date < '20210824':
                    df = pd.read_excel(f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_sp.xlsx")
                else:
                    path_all = [f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_mix_sp.xlsx",
                                f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_mix_JS_sp.xlsx",
                                f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_mix_JS_SH_sp.xlsx"]
                    df_list = []
                    for path in path_all:
                        if file_exist(path):
                            df_list.append(pd.read_excel(path))
                    df = pd.concat(df_list)
            elif portfolio == 'Kunlun_sp_pure':
                df = pd.read_excel(f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_pure_sp.xlsx")
                pure_js_path = f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_pure_JS_sp.xlsx"
                if self.st_date >= '20210813' and file_exist(pure_js_path):
                    df2 = pd.read_excel(pure_js_path)
                    df = pd.concat([df, df2])
            elif portfolio in ['Kunlun_sp_mix_o32', 'Kunlun_sp_mix_o45', 'Kunlun_sp_pure_o32', 'Kunlun_sp_pure_o45',
                               'Kunlun_sp_mix_o45_sh', 'Kunlun_sp_pure_o45_sh']:
                path_dict = {
                    'Kunlun_sp_mix_o32': f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_mix_sp.xlsx",
                    'Kunlun_sp_mix_o45': f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_mix_JS_sp.xlsx",
                    'Kunlun_sp_pure_o32': f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_pure_sp.xlsx",
                    'Kunlun_sp_pure_o45': f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_pure_JS_sp.xlsx",
                    'Kunlun_sp_mix_o45_sh': f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_mix_JS_SH_sp.xlsx",
                    'Kunlun_sp_pure_o45_sh': f"/data/user/666888/WuKong/portfolios/WuKong_{self.st_date}_pure_JS_SH_sp.xlsx"

                }
                if os.path.exists(path_dict[portfolio]):
                    df = pd.read_excel(path_dict[portfolio])
                else:
                    print(f'{self.st_date} 没有组合：{portfolio}')
                    return {}
            else:
                raise ValueError
            codes = df.iloc[:, 0].tolist()
            volumes = [int(quantity) for quantity in df.iloc[:, 3]]
        else:
            raise ValueError
        return self.__out(codes, volumes)

    def __out(self, codes, volumes):
        if self.code_filter is not None:
            for i in range(len(codes)):
                if codes[i] == self.code_filter:
                    return {self.code_filter: volumes[i]}
        code_vol_dict = dict(zip(codes, volumes))
        if self.market == 'all':
            return code_vol_dict
        elif self.market == 'sz':
            return dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SZ')])
        elif self.market == 'sh':
            return dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SH')])
        elif self.market == 'szzb':
            return dict([(x, y) for (x, y) in code_vol_dict.items() if x.startswith('0')])
        elif self.market == 'cyb':
            return dict([(x, y) for (x, y) in code_vol_dict.items() if x.startswith('3')])

# 获取用于回测的股票列表和日期列表
def get_bt_code_date(code_type, st_date, ed_date, base_date=index_base_date):
    """code_type为下面中的一个[300, 500, 800, cb]"""
    if code_type == '300':
        code_list = get_index_code('hs300', base_date)
    elif code_type == '500':
        code_list = get_index_code('zz500', base_date)
    elif code_type == '800':
        code_list = get_index_code('800', base_date)
    elif code_type == 'kcb':
        code_list = get_kcb_code(base_date, n=60)
    elif code_type == 'cyb':
        code_list = get_cyb_code(base_date, n=60)
    elif code_type == 'cb':
        code_list = list(GetCodeVol(st_date, ed_date).get_cb_code().keys())
    else:
        raise ValueError('code_type输入错误，应该为下面中的一个：[300, 500, 800, cb]')
    trading_day_list = trading_day(st_date, ed_date)
    return code_list, trading_day_list


# ----------------------------------------------------------------------------------------------
# 获取指数成分数据
def get_index_code(index="hs300", base_date=index_base_date, ed_date=None, gap=1, market='all'):
    if ed_date is None:
        date_list = [base_date]
    else:
        date_list = trading_day(base_date, ed_date)
        if gap > 1:
            date_list = list(sorted(set(list(np.array(date_list)[::gap]) + date_list[-1:])))

    code_list = []
    for trade_date in date_list:
        if index in ['hs300', 'zz500', 'zz1000']:
            index_weight = fa.hset('INDEX', str(trade_date), index.upper())
            code_list += index_weight["stock"].to_list()
        elif index in ['800', '1800']:
            index_weight300 = fa.hset('INDEX', str(trade_date), 'HS300')
            index_weight500 = fa.hset('INDEX', str(trade_date), 'ZZ500')
            code_list += index_weight300["stock"].to_list() + index_weight500["stock"].to_list()
            if index == '1800':
                index_weight1000 = fa.hset('INDEX', str(trade_date), 'ZZ1000')
                code_list += index_weight1000["stock"].to_list()
    code_list = list(sorted(set(code_list)))

    # 补丁（market），获取不同市场的数据，默认all为所有，其余还有：sh, sz, szzb, cyb, szzb, kyb
    if market == 'sh':  # 上交所股票
        code_list = [x for x in code_list if x.endswith('.SH')]
    elif market == 'sz':  # 深交所股票
        code_list = [x for x in code_list if x.endswith('.SZ')]
    elif market == 'shzb':  # 上海主板股票 6开头但不是68开头
        code_list = [x for x in code_list if x.endswith('.SH') and not x.startswith('68')]
    elif market == 'kcb':  # 科创板股票 688开头
        code_list = [x for x in code_list if x.endswith('.SH') and x.startswith('68')]
    elif market == 'szzb':  # 深圳主板股票 0开头
        code_list = [x for x in code_list if x.endswith('.SZ') and x.startswith('0')]
    elif market == 'cyb':  # 创业板股票 3开头
        code_list = [x for x in code_list if x.endswith('.SZ') and x.startswith('3')]
    return code_list


# 获取一个code_list所属成分
def get_code_index(code_list, base_date):
    code300 = get_index_code('hs300', base_date)
    code500 = get_index_code('zz500', base_date)
    code1000 = get_index_code('zz1000', base_date)
    code_index_info = []
    for code in code_list:
        if code in code300:
            code_index_info.append('hs300')
        elif code in code500:
            code_index_info.append('zz500')
        elif code in code1000:
            code_index_info.append('zz1000')
        else:
            code_index_info.append('非成分')
    return code_index_info


def get_index_weight(index="hs300", base_date=index_base_date):
    index_weight = fa.hset('INDEX', str(base_date), index.upper()).set_index("stock")['weight'] / 100
    return index_weight


def get_index_code_volume(index="hs300", base_date=index_base_date, size=5 * 1e8):
    codes, vols = [], []
    if index in ['hs300', 'zz500', 'zz1000']:
        index_weight = get_index_weight(index, base_date)
        codes, vols = get_vol_based_on_weight(index_weight, base_date, size=size)
    elif index == '800':
        index_weight300 = get_index_weight('hs300', base_date)
        codes300, vols300 = get_vol_based_on_weight(index_weight300, base_date, size=size / 2)
        index_weight500 = get_index_weight('zz500', base_date)
        codes500, vols500 = get_vol_based_on_weight(index_weight500, base_date, size=size / 2)
        codes = list(codes300) + list(codes500)
        vols = vols300 + vols500
    elif index == '1800':
        index_weight300 = get_index_weight('hs300', base_date)
        codes300, vols300 = get_vol_based_on_weight(index_weight300, base_date, size=size / 3)
        index_weight500 = get_index_weight('zz500', base_date)
        codes500, vols500 = get_vol_based_on_weight(index_weight500, base_date, size=size / 3)
        index_weight1000 = get_index_weight('zz1000', base_date)
        codes1000, vols1000 = get_vol_based_on_weight(index_weight1000, base_date, size=size / 3)
        codes = list(codes300) + list(codes500) + list(codes1000)
        vols = vols300 + vols500 + vols1000
    return codes, vols


def get_all_code(base_date, type='stock'):
    """获取两市所有股票代码"""
    code_list = []
    if type == 'stock':
        code_list = fa.hset("MARKET", base_date, "ALLA")['stock'].to_list()
    elif type == 'cb':
        code_list = cbond_set(base_date)
    return code_list


def get_cb_code(st_date, ed_date, gap=5):
    """获取转债样本"""
    code_list = []
    for i, trade_date in enumerate(trading_day(int(st_date), int(ed_date))[::-1]):
        trade_file = "/data/user/666888/WuKong/portfolios/WuKong_{}.xlsx".format(trade_date)
        if i % gap == 0 and os.path.exists(trade_file):
            df = pd.read_excel(trade_file)
            code_list += list(df['证券代码'])
    codes = list(sorted(set(code_list)))
    return codes


def get_kcb_code(base_date, n=60):
    """获取科创板股票样本，选择原则：必须在base_date前n日以前上市"""
    market_stock_list = fa.hset("MARKET", base_date, "ALLA_HIS")['stock'].to_list()
    kcb_stock_list = list(filter(lambda x: x.startswith('68'), market_stock_list))
    factor_df = fa.get_factor_value("Basic_factor", kcb_stock_list, [str(base_date)], ['listing_date'])['listing_date']
    key_date = trading_day_gap(int(base_date), -n)
    kcb_code = list(factor_df[factor_df <= key_date].index)
    return kcb_code


def get_cyb_code(base_date, n=60):
    """获取创业板股票样本，选择原则：必须在base_date前n日以前上市"""
    market_stock_list = fa.hset("MARKET", base_date, "ALLA_HIS")['stock'].to_list()
    cyb_stock_list = list(filter(lambda x: x.startswith('3'), market_stock_list))
    factor_df = fa.get_factor_value("Basic_factor", cyb_stock_list, [str(base_date)], ['listing_date'])['listing_date']
    key_date = trading_day_gap(int(base_date), -n)
    cyb_code = list(factor_df[factor_df <= key_date].index)
    return cyb_code


def get_target_industry(code_list, base_date, industry_type='CITICS', level=1):
    """
    获取股票所属的行业
    industryType: 行业类型，’CSRC’ 为证监会行业分类，’CITICS’ 为中信行业分类，’SW’ 为申万行业分类，默认全部行业。
    level:行业级别，取值[1,3]之间的整数，默认为三级行业，证监会行业只有两级分类取[1,2]的整数
    """
    industry = fa.hsi(code_list, base_date, industryType=industry_type, industryLevel=level)
    return industry


def get_industry_info(industry_type='CITICS', level=1):
    industry_info = fa.hind(industry_type, level)
    return industry_info


def get_vol_based_on_weight(index_weight: pd.Series, st_date, ed_date=None, size=5 * 1e8):
    """根据给定的指数权重，按照一段区间内价格的均值，计算权重下对应的量"""
    if ed_date is None:
        ed_date = st_date
    index_df = get_vol_based_on_weight_matrix(index_weight, st_date, ed_date, [size])
    codes = index_df.index
    vols = index_df[size].to_list()
    return codes, vols


def get_vol_based_on_weight_matrix(index_weight: pd.Series, st_date, ed_date, size_list):
    """与上面的函数get_vol_based_on_weight相比，输入一个size_list，输出每个规模下的量"""
    all_trading_days = list(map(str, trading_day(int(st_date), int(ed_date))))
    close = fa.get_factor_value("Basic_factor", index_weight.index.tolist(), all_trading_days, ["close"])['close'].unstack().mean()
    index_df = pd.concat([index_weight, close], axis=1)
    index_df.columns = ['weight', 'close']
    for size in size_list:
        index_df[size] = size * index_df['weight'] / index_df['close']  # 单位是股
    index_df = index_df[size_list].astype(int)
    return index_df


def get_order_capacity(code, st_date, ed_date, name='OrderCapacity', strategy='Albest'):
    if strategy == 'Albest':
        order_capacity_dir = f'/data/user/666888/OrderCapacity'
    elif strategy == 'Everest':
        order_capacity_dir = f'/data/user/015629/OrderCapacity'
    else:
        raise ValueError

    order_capacity = load_json_file(f'{order_capacity_dir}/{code}/{name}.json')[name]
    order_capacity_interval = dict([(x, y) for (x, y) in order_capacity.items() if st_date <= x <= ed_date])
    return order_capacity_interval


def get_enhancement_stock_pool(st_date, ed_date, n=100, strategy='Albest'):
    # 获取实盘在一段区间内，未交易的股票池列表（上市超过180天，平均日振幅大于2%，按交易额从大到小排序）
    from SP.UtilsSP.LoadSPFile import load_sp_result_by_stock
    date_list = trading_day(st_date, ed_date)
    sp_trading_code_list = []
    for trade_date in date_list:
        sp_df = load_sp_result_by_stock(trade_date, strategy)
        sp_trading_code_list += list(sp_df['证券代码'])
    sp_trading_code_list = list(set(sp_trading_code_list))

    st_date2 = trading_day_gap(st_date, -60)
    date_list2 = trading_day(st_date2, ed_date)
    all_market_code = get_all_code(trading_day_gap(st_date, -180))
    remain_code_list = list(set(all_market_code) - set(sp_trading_code_list))
    daily_data = get_stock_daily_result(remain_code_list, date_list2, ['high', 'low', 'amt'])
    daily_data['pct'] = daily_data['high'] / daily_data['low'] - 1
    daily_data = daily_data[daily_data['pct'] > 0.02][['pct', 'amt']]
    daily_data = daily_data.reset_index().groupby('stock').mean().sort_values(by='amt', ascending=False)
    select_code_list = list(daily_data.index)[:n]
    return select_code_list


# 成分股重置日期
def index_date(index_name, st_date, ed_date):
    date_list = trading_day(st_date, ed_date)
    index_date_group = []
    index_code_base = []
    for trade_date in date_list:
        index_code = get_index_code(index=index_name, base_date=trade_date)
        if index_code != index_code_base:
            index_date_group.append([trade_date, trade_date])
            add_code = set(index_code) - set(index_code_base)
            reduce_code = set(index_code_base) - set(index_code)
            print(f'成分股变更：{trade_date}，新增{len(add_code)}只标的，剔除{len(reduce_code)}只标的')
            index_code_base = index_code
        else:
            index_date_group[-1][1] = trade_date
    return index_date_group


# print(index_date('hs300', '20171201', '20211129'))
