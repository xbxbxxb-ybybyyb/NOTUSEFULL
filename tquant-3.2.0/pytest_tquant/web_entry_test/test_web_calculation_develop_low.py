import os
os.environ['start_date'] = '2019/01'
os.environ['end_date'] = '2019/04'
os.environ['scene'] = 'calc'
os.environ['DSWMAP_workspaceId'] = '4cf4b283246e4fa4824a9d4772fae'

if os.environ.get("exec_env") == 'prd':
    os.environ['uuid'] = '2758e0ee-b3e0-4501-8902-803f5b32e51c'
    os.environ['factor_name'] = 'test0622'
    os.environ['file_path'] = './factors'
    os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
    os.environ['project_id'] = 'd934130170e0435b85064fe21281ba0d'
    os.environ['developer'] = 'lhyj_lianghuaprd'
    os.environ['sample_inner_startdate'] = '2015/01'
    os.environ['sample_inner_enddate'] = '2019/12'
elif 'dev' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'dev-uat'
    os.environ['uuid'] = 'ed63b645-55ac-4fb7-ad52-a3e964218904'
    os.environ['factor_name'] = 'testtest'
    os.environ['file_path'] = '/app/mount/code'
    os.environ['space_id'] = '24aa13e77637449099184b8bb75c3d72'
    os.environ['project_id'] = 'a0adadcd838a469e9eac5cfe1d59620b'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['sample_inner_startdate'] = '2018/01'
    os.environ['sample_inner_enddate'] = '2019/12'
elif 'sit' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'sit-uat'
    os.environ['uuid'] = 'ed63b645-55ac-4fb7-ad52-a3e964218904'
    os.environ['file_path'] = './factors'
    os.environ['factor_name'] = 'testnsw'
    os.environ['project_id'] = '563d085a96124a6b809b50d7bdd1c591'
    os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['sample_inner_startdate'] = '2018/01'
    os.environ['sample_inner_enddate'] = '2019/12'



import time
import sys
import calendar
sys.path.append('../')
sys.path.append('./')

# from FactorProvider.conf.TDubboConf import get_jurisdictionData
from web_entry.utils import web_calculation

start_time = time.time()
factor_name = os.environ.get('factor_name')
origin_start_date = os.environ.get('start_date')
origin_end_date = os.environ.get('end_date')
file_path = os.environ.get('file_path')
sample_inner_startdate = os.environ.get('sample_inner_startdate')
sample_inner_enddate = os.environ.get('sample_inner_enddate')

if sample_inner_startdate and sample_inner_enddate:
    origin_start_date_tmp = origin_start_date.split('/')
    start_date = '{}{}{}'.format(origin_start_date_tmp[0], origin_start_date_tmp[1],
                                 '01')
    origin_end_date_tmp = origin_end_date.split('/')
    last_day_of_month = str(
        calendar.monthrange(int(origin_end_date_tmp[0]), int(origin_end_date_tmp[1]))[
            1])
    end_date = '{}{}{}'.format(origin_end_date_tmp[0], origin_end_date_tmp[1],
                               last_day_of_month)
    sample_inner_startdate = sample_inner_startdate.replace('/', '') + '01'
    sample_inner_enddate = sample_inner_enddate.replace('/', '') + '31'
    if start_date < sample_inner_startdate:
        raise Exception('开始时间{}小于样本内起始时间{}'.format(start_date, sample_inner_startdate))
    if end_date > sample_inner_enddate:
        raise Exception('结束时间{}大于样本内结束时间{}'.format(end_date, sample_inner_enddate))
else:
    print('环境变量sample_inner_startdate或sample_inner_enddate不存在')

try:
    web_calculation(factor_name, origin_start_date, origin_end_date, file_path, 'research',
                    mode='save', dynamic_load_attr=False)
except Exception as e:
    raise e
finally:
    end_time = time.time()
    print('produceTime', end_time - start_time)