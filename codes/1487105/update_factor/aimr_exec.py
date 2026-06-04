import pandas as pd 
import datetime
import time 
from xquant.compute.aimr import AIMR
import sys 
sys.path.insert(0,'update_factor/')
from update_factor_exector import *
argus = pd.read_pickle(update_factor_help_path+'start_end_date.pkl')
today = datetime.date.today().strftime('%Y%m%d')
t0= time.time()
batch_factor=AIMR.getParam()

if(not 'start_date' in argus.keys()):
    argus['start_date']=today
if(not 'end_date' in argus.keys()):
    argus['end_date']=today
if(type(argus['start_date'])==int):
    argus['start_date']=str(argus['start_date'])
if(type(argus['end_date'])==int):
    argus['end_date']=str(argus['end_date'])
t0=time.time()
catalog_type=['daily']
multi_flag = False
for t in catalog_type:
    if not os.path.exists(factor_data_path+t+'/'):
        os.makedirs(factor_data_path+t+'/')
    factor_list=catalog_factor(factor_management_path,'.json',t)
    this_factor_list = pd.read_pickle(aimr_factor_dict_path)[batch_factor]
    factor_list = sorted(list(set(factor_list)&set(this_factor_list)))
    print(len(factor_list),' nums factor is updating ',argus['start_date'],argus['end_date'])
    if 'multi' in batch_factor:
        multi_flag = True
    update_factor(factor_list,argus['start_date'], argus['end_date'],multi_flag)
    success_update_factors,fail_update_factors = check_factor_update_success(factor_list,t,argus['start_date'],argus['end_date']) 
    print("update "+t+" finished,cost "+str(time.time()-t0)+" s")
    print(str(len(fail_update_factors))+' factor updated fail.')
    print(str(fail_update_factors)+' updated fail.')
print('cost time',time.time()-t0)

change_permission(factor_data_path)
