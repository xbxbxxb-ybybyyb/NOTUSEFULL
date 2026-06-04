import os
os.environ['scene'] = 'test'
os.environ['freq'] = 'DAY'
os.environ["custom_standard"] = '3'

os.environ['DSWMAP_workspaceId'] = '4cf4b283246e4fa4824a9d4772fae'

if os.environ.get("exec_env") == 'prd':
    os.environ['file_path'] = './factors'
    os.environ['uuid'] = '47273f7b-288b-4b6f-aa95-f7707cb97225'
    os.environ['factor_id'] = '32'
    os.environ['factor_name'] = 'testnsw'
    os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
    os.environ['developer'] = 'lhyj_default'
    os.environ['factor_type'] = '\\u884C\\u60C5'
    os.environ['security_type'] = '1'
    os.environ['day_lag'] = '1'
    os.environ['quarter_lag'] = '1'
    os.environ['depend_factor'] = 'high:0,low:0,open:0,close:0'
    os.environ['stock_universe'] = 'alpha_universe'
elif 'dev' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'dev-uat'
    os.environ['file_path'] = '/app/mount/code'
    os.environ['uuid'] = '0ed5b12d-0d66-4a97-b5b3-55f9f38090e6'
    os.environ['factor_id'] = '5'
    os.environ['factor_name'] = 'testtest'
    os.environ['space_id'] = '24aa13e77637449099184b8bb75c3d72'
    os.environ['developer'] = 'lhyj_default'
    os.environ['factor_type'] = '\\u884C\\u60C5'
    os.environ['security_type'] = '1'
    os.environ['day_lag'] = '5'
    os.environ['quarter_lag'] = '1'
    os.environ['depend_factor'] = 'high:0,low:0,open:0,close:0'
    os.environ['stock_universe'] = 'alpha_universe'
elif 'sit' in os.environ.get("exec_env"):
    os.environ['exec_env'] = 'sit-uat'
    os.environ['file_path'] = './factors'
    os.environ['uuid'] = '0ed5b12d-0d66-4a97-b5b3-55f9f38090e6'
    os.environ['factor_id'] = '5'
    os.environ['factor_name'] = 'testnsw'
    os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
    os.environ['developer'] = 'lhyj_default'
    os.environ['factor_type'] = '\\u884C\\u60C5'
    os.environ['security_type'] = '1'
    os.environ['day_lag'] = '5'
    os.environ['quarter_lag'] = '1'
    os.environ['depend_factor'] = 'high:0,low:0,open:0,close:0'
    os.environ['stock_universe'] = 'alpha_universe'

from web_entry.web_tester_release import factor_tester

excess_return_path = '/app/mount/factor_return'
if not os.path.exists(excess_return_path):
    os.makedirs(excess_return_path)

factor_tester()
