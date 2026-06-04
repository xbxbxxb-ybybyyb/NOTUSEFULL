from SmartFactor.psfactor import FactorData as XFactorData
from SmartFactor.calculation.DataCalculation import run_securities_days

xps = XFactorData()
#
# # 创建因子库
# # # 高频: T+0, 低频: Alpha
# print(xps.create_factor_library('test_high', 'T+0'))
# # # #
# # # # 新增因子:
# print(xps.add_factor('test_high', {'hfrefactor':'float'}))


#计算因子，并返回
res = run_securities_days(factor_list=['hfrefactor'], security_list=['688001.SH', "000001.SZ"],
                           security_type='stock', library_name='test_high',
                          start_date='20200102', end_date='20200108',
                          return_mode='show', file_path='./SmartFactor/factors')
print(res)
print(res['688001.SH'].columns)

#计算因子，并入库
res = run_securities_days(factor_list=['hfrefactor'], security_list=['688001.SH', "000001.SZ"],
                           security_type='stock', library_name='test_high',
                          start_date='20200102', end_date='20200108',
                          return_mode='save', file_path='./SmartFactor/factors')


res = xps.get_factor_value('test_high',['20200102','20200120'],['688001.SH'],["hfrefactor"])
print(res)



