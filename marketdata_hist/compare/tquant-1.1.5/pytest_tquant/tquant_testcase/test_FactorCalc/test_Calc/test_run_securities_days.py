from tquant.SmartFactor.FactorCalc import run_securities_days
import os
import pytest

path_dir = str(os.path.abspath(os.path.join(os.path.dirname(__file__))))


def test_run_securities_days_show():
    run_securities_days(factor_list=['high1', 'high2'],
                        start_date='20200512', end_date='20200530',
                        library_name='high_20180808', return_mode='save',
                        file_path=path_dir)


def test_run_securities_days_save():
    res = run_securities_days(factor_list=['high1', 'high2'],
                              start_date='20200512', end_date='20200530',
                              library_name='high_20180808', return_mode='show',
                              file_path=path_dir)
    assert isinstance(res, dict)


if __name__ == "__main__":
    pytest.main(['-v'])
