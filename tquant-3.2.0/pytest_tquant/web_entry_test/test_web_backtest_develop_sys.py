import os

os.environ['scene'] = 'backtest'
os.environ['universe'] = 'alpha_universe'
os.environ['benchmark'] = 'alpha_universe'
os.environ['industry_type'] = 'CITIC_I'
os.environ['median'] = '1'
os.environ['standard'] = '1'
os.environ['fillna'] = '1'
os.environ['direction'] = 'long-only'
os.environ['segment_number'] = '10'
os.environ['holding_period'] = '1'
os.environ['seg_by_industry'] = '1'
os.environ['filter_max'] = '1'
os.environ['transaction_cost'] = '0.0013'
os.environ['start_date'] = '2019/01/02'
os.environ['end_date'] = '2019/04/30'
os.environ['DSWMAP_workspaceId'] = '4cf4b283246e4fa4824a9d4772fae'
os.environ['neutralize'] = "1"

if os.environ.get("exec_env") == 'prd':
    os.environ['file_path'] = './factors'
    os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
    os.environ['project_id'] = 'd934130170e0435b85064fe21281ba0d'
    os.environ['developer'] = 'lhyj_lianghuaprd'
    os.environ['uuid'] = '99c6c1a4-d78a-4643-8ce2-526eea77d40c'
    os.environ['factor_id'] = '49'
    os.environ['factor_name'] = 'test0622'
elif 'dev' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'dev-uat'
    os.environ['file_path'] = '/app/mount/code'
    os.environ['space_id'] = '24aa13e77637449099184b8bb75c3d72'
    os.environ['project_id'] = 'a0adadcd838a469e9eac5cfe1d59620b'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['uuid'] = '857ddd74-307d-41ca-9749-f604e08ca7b4'
    os.environ['factor_id'] = '5'
    os.environ['factor_name'] = 'testtest'
elif 'sit' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'sit-uat'
    os.environ['file_path'] = './factors'
    os.environ['project_id'] = '563d085a96124a6b809b50d7bdd1c591'
    os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['uuid'] = '857ddd74-307d-41ca-9749-f604e08ca7b4'
    os.environ['factor_id'] = '5'
    os.environ['factor_name'] = 'testnsw'

from web_entry.web_backtest_develop_sys import backtest_release

backtest_release()
