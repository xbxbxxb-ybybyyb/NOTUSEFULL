from SmartFactor.psfactor import FactorData as XFactorData

xps = XFactorData()
#
# # 创建因子库
# # 高频: T+0, 低频: Alpha
# print(xps.create_factor_library('test_high', 'T+0'))
# #
# # 新增因子:
# print(xps.add_factor('test_high', {'hfrefactor':'float'}))


res = xps.get_factor_value('test_high',['20200102','20200108'],['688001.SH'],["hfrefactor"])
print(res)

