import pytest
import os
path_dir = str(os.path.abspath(os.path.join(os.path.dirname(__file__))))


@pytest.fixture(scope='session')
def update_calc_environ(exec_env='dev-prd', file_path=path_dir):
    """
    计算环境
    """
    os.environ['exec_env'] = exec_env
    os.environ['uuid'] = '159ae39b-a815-4232-970d-29b5b463a4ad'
    os.environ['start_date'] = '2018/01'
    os.environ['end_date'] = '2020/01'
    os.environ['file_path'] = file_path
    os.environ['space_id'] = '8b0c4ac8b572464fb758883f1afdce63'
    os.environ['project_id'] = 'ae1ff591f612476f89b52a5cf3e6b8d1'
    os.environ['developer'] = 'xxh001_default'
    os.environ['sample_inner_startdate'] = '2018/01/01'
    os.environ['sample_inner_enddate'] = '2020/01/31'


@pytest.fixture(scope='session')
def update_backtest_environ(exec_env='dev-prd'):
    """
    回测环境
    """
    os.environ['exec_env'] = exec_env
    os.environ['uuid'] = '31be5c35-945a-4cbd-85d0-b5687afc5d5e'
    os.environ['factor_id'] = '110'
    os.environ['factor_name'] = 'test_weyue'
    os.environ['universe'] = 'hs300'
    os.environ['benchmark'] = 'hs300'
    os.environ['industry_type'] = 'CITIC_I'
    os.environ['median'] = '1'
    os.environ['standard'] = '1'
    os.environ['fillna'] = '1'
    os.environ['direction'] = 'long-short2'
    os.environ['segment_number'] = '5'
    os.environ['holding_period'] = '20'
    os.environ['seg_by_industry'] = '0'
    os.environ['filter_max'] = '1'
    os.environ['transaction_cost'] = '0.0023'
    os.environ['start_date'] = '2019/05'
    os.environ['end_date'] = '2019/08'
    os.environ['space_id'] = '8b0c4ac8b572464fb758883f1afdce63'
    os.environ['project_id'] = 'ae1ff591f612476f89b52a5cf3e6b8d1'
    os.environ['developer'] = 'xxh001_default'
    os.environ['sample_inner_startdate'] = '2018/01/01'
    os.environ['sample_inner_enddate'] = '2021/12/31'
