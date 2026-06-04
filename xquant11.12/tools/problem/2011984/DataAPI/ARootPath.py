class RootPath:
    def __init__(self):
        self.__user_id = '011668'
        self.strategy_list = ['Albest', 'Everest', 'Kunlun']
        self.portfolio_list = ['hs300', 'zz500', 'kcb', 'Albest_sp', 'Everest_sp', 'Kunlun_sp', 'Kunlun_mix', 'Kunlun_pure']

        self.stock_origin_data_path = '/data/user/666888/TradeData2/'  # 股票数据源文件路径
        self.cb_origin_data_path = '/data/user/666888/TradeDataCB3/'  # 转债数据源文件路径
        self.origin_data_path_l2p = '/data/user/015629/LiveL2PTradeData/'

        self.__sp_data_path = '/data/user/011668/SP_Data'
        self.__sp_trading_path = '/data/user/011668/SP_Data/OriginData'
        self.__sp_trading_resolve_path = '/data/user/011668/SP_Data/ResolveData'

    def get_origin_data_path(self, portfolio):
        if get_asset_class(portfolio) == 'cb':
            return self.cb_origin_data_path
        elif get_asset_class(portfolio) == 'stock':
            return self.stock_origin_data_path
        elif get_asset_class(portfolio) in ['stock_l2p', 'cb_l2p']:
            return self.origin_data_path_l2p
        else:
            raise ValueError

    def get_sp_data_path(self):
        return self.__sp_data_path

    def get_sp_trading_path(self, portfolio=''):
        return f'{self.__sp_trading_path}/{portfolio}'

    def get_sp_trading_resolve_path(self, portfolio=''):
        return f'{self.__sp_trading_resolve_path}/{portfolio}'


# 获取portfolio所属的资产大类，cb为可转债，stock为股票
def get_asset_class(portfolio):
    p = portfolio.lower()
    if 'kunlun' in p or p in ['cb_sp']:
        return 'cb'
    elif 'albest' in p or 'everest' in p or p in ['hs300', 'zz500', '800', 'zz1000', 'cyb', 'kcb', 'stock_sp',
                                                  'cyb_l2p', 'exclude_sp', 'stock_test', 'margin']:
        return 'stock'
    elif p == 'stock_sp_l2p':
        return 'stock_l2p'
    elif p == 'cb_sp_l2p':
        return 'cb_l2p'
    else:
        raise ValueError('未找到portfolio对应的资产大类')


# 获取portfolio所属的策略，输出Algo/Easy/WuKong中的一个
def get_strategy_class(portfolio):
    portfolio_strategy_dict = {
        'algo_sp': 'Algo',
        'easy_sp': 'Easy',
        'wukong_sp': 'WuKong'
    }
    if portfolio in portfolio_strategy_dict.keys():
        return portfolio_strategy_dict[portfolio]
    return portfolio


# 手续费
cost_rate = {'stock_buy': 0.0000887, 'stock_sell': 0.0010887, 'cb_sh': 1 / 1000000, 'cb_sz': 4 / 100000}
