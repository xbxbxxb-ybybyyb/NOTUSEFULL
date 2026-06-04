from SmartFactor.HFBaseFactor import HFBaseFactor
import talib as ta

# 自定义高频因子类，定义相关类属性，重写calc方法，确定计算逻辑。
class fund15(HFBaseFactor):
    factor_type = "TICK"  # 目前仅支持tick级高频因子的开发
    factor_name = 'fund15'
    security_type = 'stock' #目前仅支持stock和fund两种证券类型
    security_pool = ['000001.SZ'] #
    depend_factor = []  # 依赖的个人因子
    custom_params = {"interval_seconds":60, "sample_period":3}  #

    def calc(self, price_data, factor_data, custom_params):
        df = price_data['tick']
        interval_seconds = custom_params["interval_seconds"]
        sample_period = custom_params["sample_period"]
        n_tick = interval_seconds//sample_period
        df['value'] = ta.ROC(df['LastPx'].values, timeperiod=n_tick)
        res = df['value'] * 0.8
        res.index = df['MDTime']
        return res
if __name__=='__main__':
    # 示例1 ： 不再派生子类。
    fac = fund15()
    res = fac.run_hfre_factor_value("20200101", "20200110", dynamic_load_attr=False)
    print(res)