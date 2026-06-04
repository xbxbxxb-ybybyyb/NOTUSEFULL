from tquant.SmartFactor.FactorCalc import run_factors_days
import os
import pytest

path_dir = str(os.path.abspath(os.path.join(os.path.dirname(__file__))))


def test_run_factors_days_show():
    run_factors_days(factor_list=['low1', 'low2', 'low3'],
                     start_date='20191102', end_date='20191114',
                     return_mode='show', num_cpus=4, file_path=path_dir)


def test_run_factors_days_save():

    res = run_factors_days(factor_list=['low1', 'low2', 'low3'],
                           start_date='20191101', end_date='20191104',
                           library_name='low_20180808', return_mode='save', file_path=path_dir)
    assert isinstance(res, dict)


if __name__ == "__main__":
    pytest.main(['-v'])
