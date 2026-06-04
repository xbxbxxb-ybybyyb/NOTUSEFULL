from tquant import PsFactorData
from SmartFactor.calculation.DataCalculation import run_securities_days
import os
import time

start_time = time.time()
tps = PsFactorData()
os.environ['DSWMAP_workspaceId'] = '4cf4b283246e4fa4824a9d4772fae'

if os.environ.get("exec_env") == 'prd':
    os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
    os.environ['project_id'] = 'd934130170e0435b85064fe21281ba0d'
    try:  # 入参是标签名组成的列表， 可以一次传入多个标签名。
        tps.add_label(['label_multi_sam'])
    except:
        run_securities_days(factor_list=['label_multi_sam'], start_date='20190101', end_date='20190228',
                            factor_type='label', dynamic_load_attr=False,
                            library_name='', return_mode='save', file_path='./factors/')
    finally:
        end_time = time.time()
        print('produceTime', end_time - start_time)
elif os.environ.get("exec_env") == 'sit-uat':
    os.environ['project_id'] = '563d085a96124a6b809b50d7bdd1c591'
    os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
    try:  # 入参是标签名组成的列表， 可以一次传入多个标签名。
        tps.add_label(['Label_test'])
    except:
        run_securities_days(factor_list=['Label_test'], start_date='20190101', end_date='20190228',
                            factor_type='label', dynamic_load_attr=False,
                            library_name='', return_mode='save', file_path='./factors/')
    finally:
        end_time = time.time()
        print('produceTime', end_time - start_time)