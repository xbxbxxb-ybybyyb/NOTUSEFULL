from SmartFactor.HFBaseFactor import HFBaseFactor


# 自定义高频因子类，定义相关类属性，重写calc方法，确定计算逻辑。
class hfrefactor(HFBaseFactor):
    factor_type = "TICK"  # 目前仅支持tick级高频因子的开发
    factor_name = 'hfrefactor'
    security_type = 'stock'  # 目前仅支持stock和fund两种证券类型
    security_pool = ['000001.SZ']  #
    depend_factor = []  # 依赖的个人因子
    custom_params = {"interval_seconds": 60, "sample_period": 3}  #
    external_data_filepath = []  # 用户依赖的外部数据文件
    external_data_memory_id_list = []
    data_input_mode = ['TICK_RAW', 'TRANSACTION_RAW']

    def calc(self, price_data, factor_data, custom_params):
        # import  copy
        # price_data_copy = copy.deepcopy(price_data)
        price_data = price_data['tick']

        interval_seconds = custom_params["interval_seconds"]
        sample_period = custom_params["sample_period"]
        n_tick = interval_seconds // sample_period

        res = price_data['LastPx'].diff(n_tick) / price_data['LastPx'].shift(n_tick) * 1000
        res.index = price_data['MDTime']

        return res
        # calc方法的返回值为pandas.Series格式，形如：
        #  MDTime
        #  145100000    2.270986e-02
        #  145103000    2.340241e-01
        #  145106000    2.588957e-01
        #  145109000    2.735518e-01
        #  145112000    2.577173e-01
        #  145115000    3.218792e-01
        #  145118000   -1.026219e-01
        #  145121000   -5.907522e-01
        #  145124000   -5.804177e-01


if __name__ == '__main__':
    # 示例1 ： 不再派生子类。
    fac = hfrefactor()
    res = fac.run_hfre_factor_value("20191104", "20191105")
    print(res)
