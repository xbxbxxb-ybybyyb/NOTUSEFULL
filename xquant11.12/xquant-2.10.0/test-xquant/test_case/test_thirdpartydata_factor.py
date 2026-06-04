import unittest

from version_control import version_number

if version_number == 0:
    from xquant.factor import FactorData
    from xquant.factor.FactorEnum import *
else:
    from xquant.thirdpartydata.factor import FactorData
    from xquant.thirdpartydata.factor.FactorEnum import *



class test_factor(unittest.TestCase):

    def testdemo(self):
        fa = FactorData(timeout=60 * 30)
        # 读取因子数据
        # 查询==》因子为"pre_close","high","open"  股票为"000001","000002","000004"  时间为 "20180502"到"20180504"
        re3 = fa.getData(["pre_close", "high", "open"], ("20180501", "20180531"),
                         ["000001.sz", "000002.sz", "000004.sz"])
        print(re3)

        # 查询所有未停牌的股票
        re6 = fa.stockFilter('20180611', FILT_TYPE.SUSPENSION)
        print(str(len(re6)), str(re6))

        re7 = fa.tradingDay('20180601', '20180631')
        print(re7)
