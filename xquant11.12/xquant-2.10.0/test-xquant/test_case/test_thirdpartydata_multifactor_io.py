import unittest

from version_control import version_number

if version_number == 0:
    from xquant.multifactor.IO.IO import *
else:
    from xquant.thirdpartydata.multifactor.IO import *



class TestIO(unittest.TestCase):

    def test_demo(self):
        print(str_date_parser('20190115'))
        # 若需读取universe_complete.h5的因子数据，则令alt="universe_complete"
        alt = "universe_complete"
        df = read_data([20131115, 20131118], alt=alt)
        print(df.head())
