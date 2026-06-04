from SmartFactor.BaseFactor import Factor


class test_weyue(Factor):

    def calc(self, factor_data):
        # TODO: 待实现的因子类方法
        # 返回的低频因子res格式：pandas.Series [index : 标的 value: 因子值]
        res = factor_data['BasicDayFactor.open'] + factor_data['BasicDayFactor.close']
        res = res.iloc[-1]
        return res