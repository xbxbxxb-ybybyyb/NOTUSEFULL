from tquant.SmartFactor.BaseFactor import Factor


class low4(Factor):
    """
    BasicFinancialFactor 财务因子测试与日频
    """
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'low4'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2  # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    # 财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["BasicDayFactor.open", "BasicFinancialFactor.eps_diluted", "BasicFinancialFactor.eps_diluted2"]
    security_pool = ['002314.SZ', '600422.SH', '603369.SH', '601658.SH']       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    def calc(self, factor_data):
        open = factor_data["BasicDayFactor.open"]
        yoyeps_diluted = factor_data["BasicFinancialFactor.eps_diluted"]
        yoyocfps = factor_data["BasicFinancialFactor.eps_diluted2"]
        part1 = (open + yoyeps_diluted + yoyocfps)
        return part1.iloc[-1]