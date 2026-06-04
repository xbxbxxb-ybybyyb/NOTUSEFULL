import unittest

from sample_strategy import MyStrategy

from version_control import version_number

if version_number == 0:
    from xquant.backtest.execute import run
else:
    from xquant.strategy.backtest.execute import run



class TestBacktest(unittest.TestCase):

    def test_demo(self):
        my_strategy = MyStrategy()
        run(my_strategy)
