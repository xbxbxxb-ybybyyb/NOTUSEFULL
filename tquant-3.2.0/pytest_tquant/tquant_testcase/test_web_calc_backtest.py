import os
import pytest


@pytest.mark.run(order=-3)
def test_web_calc():
    """
    普通计算脚本测试
    :return:
    """
    os.environ['scene'] = 'Calc'
    os.system(r'/opt/anaconda3/bin/python3.6 -u /opt/anaconda3/lib/python3.6/site-packages/web_entry/web_calculation_devlop.py')


@pytest.mark.parametrize('transaction_cost', ['0.0023', '0.0'])
@pytest.mark.parametrize('holding_period', ['1', '30'])
@pytest.mark.parametrize('segment_number', ['5', '10'])
@pytest.mark.parametrize('benchmark', ['zz500', 'hs300', 'sz50', 'alpha_universe'])
@pytest.mark.parametrize('universe', ['zz500', 'hs300', 'sz50', 'alpha_universe'])
@pytest.mark.run(order=-2)
def test_web_backtest(universe, benchmark, segment_number, holding_period, transaction_cost):
    """
    普通回测脚本测试
    :param universe:
    :param benchmark:
    :param segment_number:
    :param holding_period:
    :param transaction_cost:
    :return:
    """
    os.environ['scene'] = 'backtest'
    os.environ['universe'] = universe
    os.environ['benchmark'] = benchmark
    os.environ['segment_number'] = segment_number
    os.environ['holding_period'] = holding_period
    os.environ['transaction_cost'] = transaction_cost
    os.system(r'/opt/anaconda3/bin/python3.6 -u /opt/anaconda3/lib/python3.6/site-packages/web_entry/web_backtest_devlop.py')


@pytest.mark.run(order=-1)
def test_web_sys_backtest():
    """
    系统检测测试（发布）
    :return:
    """
    os.environ['scene'] = 'backtest'
    os.environ['start_date'] = '2019/06/01'
    os.environ['end_date'] = '2020/01/13'
    os.system(r'/opt/anaconda3/bin/python3.6 -u /opt/anaconda3/lib/python3.6/site-packages/web_entry/web_backtest_develop_sys.py')
