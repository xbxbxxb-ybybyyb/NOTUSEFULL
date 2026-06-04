import os

os.environ['exec_env'] = 'uat'
os.environ['scene'] = 'backtest'
os.environ['uuid'] = 'a3a0c3d0-1dd7-4075-9bbb-a245aed618cc'
os.environ['factor_id'] = '5'
os.environ['factor_name'] = 'testnsw'
os.environ['universe'] = 'alpha_universe'
os.environ['benchmark'] = 'hs300'
os.environ['industry_type'] = 'CITIC_I'
os.environ['median'] = '1'
os.environ['standard'] = '1'
os.environ['fillna'] = '1'
os.environ['direction'] = 'long-only'
os.environ['segment_number'] = '10'
os.environ['holding_period'] = '1'
os.environ['seg_by_industry'] = '1'
os.environ['filter_max'] = '1'
os.environ['transaction_cost'] = '0'
os.environ['start_date'] = '2019/01'
os.environ['end_date'] = '2019/04'
os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
os.environ['project_id'] = '04c1cba8ea3b44bfae20873beda962a7'
os.environ['developer'] = 'lhyj_lianghuauat'
os.environ['sample_inner_startdate'] = '2019/01'
os.environ['sample_inner_enddate'] = '2020/12'


os.environ['file_path'] = './factors'


import calendar
import pandas as pd
import datetime as dt
import json
from tquant.psfactor import PsFactorData
from factor_interface import get_factor_value_by_library_defalt
from tquant import BasicData
from tquant import StockData
from kafka import KafkaProducer
from kafka.errors import KafkaError

def get_factor_value_by_library_normal():
    start_date = os.environ.get('start_date')
    end_date = os.environ.get('end_date')
    factor_name = os.environ.get('factor_name', 'ZaoYinTrader')
    Library_env = 'research'
    security_list = None
    sort = False
    df = get_factor_value_by_library_defalt(start_date, end_date, factor_name, library_env=Library_env,
                                            Security_list=security_list, Sort=sort)

    print(df)

if __name__ == "__main__":
    get_factor_value_by_library_normal()
