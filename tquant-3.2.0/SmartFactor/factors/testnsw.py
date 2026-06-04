from SmartFactor.BaseFactor import Factor

class testnsw(Factor):
    """
    (-1 * DELTA((((CLOSE - LOW) -  (HIGH - CLOSE)) / (HIGH - LOW)), 1))
    """
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'testnsw'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2 # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    #财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["market.close", "market.low", "market.high"]  # 设置依赖因子
    security_pool = "SZA"       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    # factor_data: dict key: 因子名 value: 因子截面 DataFrame
    def calc(self, factor_data):
        close = factor_data['BasicDayFactor.close']
        low = factor_data['BasicDayFactor.low']
        high = factor_data['BasicDayFactor.high']
        part1 = (2 * close - low - high) / (high - low)
        result = part1.diff(1).iloc[-1] * (-1)
        return result



#调用调试接口run_day_factor_value(),根据calc方法中的计算逻辑，计算起止时间内的因子值，并以DataFrame的格式返回计算结果。
if __name__=='__main__':
    dayfactor = testnsw()
    # run_day_factor_value中包含参数dynamic_load_attrs
    df = dayfactor.run_day_factor_value(start_date='20191102', end_date='20191114',dynamic_load_attr=False)
    print(df)