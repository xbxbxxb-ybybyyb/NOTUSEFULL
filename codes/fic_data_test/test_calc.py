import os
import time
library_name = 'nsw_test'
os.environ["DSWMAP_username"] = '013150'
os.environ["ENV_VERSION"] = ''
os.environ['DSWMAP_envTag'] = 'prd'

from tquant import PsFactorData
tps = PsFactorData()
#print(tps.create_factor_library(library_name,'T+0'))
##print(tps.create_factor_library(library_name, 'Alpha'))
print(tps.get_library_info())

factor_list = ['pxchange'+str(i) for i in range (5)]
factor_dict = {}
for i in factor_list:
	factor_dict[i]='double'

tps.add_factor(library_name,factor_dict)
# # 获取高频因子名
#from tquant import StockData
#sd = StockData()
# df13_1 = sd.get_stock_tick('000001.SZ', '20191129 093000000', '20191129 150000250')
# hfre_factor = df13_1.columns.to_list()
# hfre_factor_dict = {}
# for i in hfre_factor:
#     if i in ['MDDate','MDTime','HTSCSecurityID']:
#         continue
#     if df13_1[i].dtypes in ['float64','int64']:
#         hfre_factor_dict[i] = 'double'
# print(hfre_factor_dict)
    
# # # # # 增加因子 
#tps.add_factor(library_name, {'new_alpha2':'double'})

# 低频因子的数据恢复性能测试
#factor_list = ['alpha2','open','high','low','close']
#from tquant.SmartFactor.FactorCalc import run_factors_days, run_securities_days
#start_date = '20180102'
#end_date_list = ['20200102']#,'20190102', '20200102']
#for end_date in end_date_list:
#	start_time = time.time()
#	res = run_factors_days(factor_list=factor_list, start_date=start_date, end_date=end_date, num_cpus=16, file_path='./factor', dynamic_load_attr=False, library_name='nsw_test2_low', return_mode='save')
#	print("time cost: "+str(time.time()-start_time))
	#print(res['alpha2'].shape)


# 高频因子的数据恢复性能测试


#from tquant import PsFactorData
#tps = PsFactorData()
#print(tps.get_library_info())     
#tps.add_factor('nsw_test2_low',{'alpha3':'double'})  
