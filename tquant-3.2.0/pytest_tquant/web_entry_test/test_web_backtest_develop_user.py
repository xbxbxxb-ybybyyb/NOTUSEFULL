import os
import random
universe_list = ['hs300', 'zz500', 'sz50', 'alpha_universe']
os.environ['universe'] = random.choice(universe_list)

benchmark_list = ['hs300', 'zz500', 'sz50', 'alpha_universe']
os.environ['benchmark'] = random.choice(benchmark_list)
industry_type_list = ['CITIC_I', 'null']
os.environ['industry_type'] = random.choice(industry_type_list)

median_list = ['1', '0']
os.environ['median'] = random.choice(median_list)

standard_list = ['1', '0']
os.environ['standard'] = random.choice(standard_list)

fillna_list = ['1', '0']
os.environ['fillna'] = random.choice(fillna_list)

os.environ['direction'] = 'long-only'

segment_number_list = ['10', '5']
os.environ['segment_number'] = random.choice(segment_number_list)

holding_period_list = ['1', '10']
os.environ['holding_period'] = random.choice(holding_period_list)

seg_by_industry_list = ['1', '0']
os.environ['seg_by_industry'] = random.choice(seg_by_industry_list)

filter_max_list = ['1', '0']
os.environ['filter_max'] = random.choice(filter_max_list)

transaction_cost_list = ['0', '0.0013', '0.0023']
os.environ['transaction_cost'] = random.choice(transaction_cost_list)

neutralize_list = ['1', '0']
os.environ['neutralize'] = random.choice(neutralize_list)

os.environ['start_date'] = '2019/01'
os.environ['end_date'] = '2019/04'
os.environ['scene'] = 'backtest'
os.environ['DSWMAP_workspaceId'] = '4cf4b283246e4fa4824a9d4772fae'
os.environ['segment_switch'] = '1'
os.environ['ret_stability'] = '1'
if os.environ.get("exec_env") == 'prd':
    os.environ['file_path'] = './factors'
    os.environ['uuid'] = '99c6c1a4-d78a-4643-8ce2-526eea77d40c'
    os.environ['factor_id'] = '49'
    os.environ['factor_name'] = 'test0622'
    os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
    os.environ['project_id'] = 'd934130170e0435b85064fe21281ba0d'
    os.environ['developer'] = 'lhyj_lianghuaprd'
    os.environ['sample_inner_startdate'] = '2015/01'
    os.environ['sample_inner_enddate'] = '2020/12'
elif 'dev' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'dev-uat'
    os.environ['file_path'] = '/app/mount/code'
    os.environ['uuid'] = 'a3a0c3d0-1dd7-4075-9bbb-a245aed618cc'
    os.environ['factor_id'] = '5'
    os.environ['factor_name'] = 'testtest'
    os.environ['space_id'] = '24aa13e77637449099184b8bb75c3d72'
    os.environ['project_id'] = 'a0adadcd838a469e9eac5cfe1d59620b'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['sample_inner_startdate'] = '2019/01'
    os.environ['sample_inner_enddate'] = '2020/12'
elif 'sit' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'sit-uat'
    os.environ['file_path'] = './factors'
    os.environ['uuid'] = 'a3a0c3d0-1dd7-4075-9bbb-a245aed618cc'
    os.environ['factor_id'] = '5'
    os.environ['factor_name'] = 'testnsw'
    os.environ['project_id'] = '563d085a96124a6b809b50d7bdd1c591'
    os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['sample_inner_startdate'] = '2019/01'
    os.environ['sample_inner_enddate'] = '2020/12'




from web_entry.web_backtest_develop_user import backtest_develop

backtest_develop()
