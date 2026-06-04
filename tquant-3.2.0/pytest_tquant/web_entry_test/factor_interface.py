import os
import json
from SmartFactor.calculation.DataCalculation import run_factors_days, run_securities_days
# from SmartFactor.FactorCalc import run_factors_days, run_securities_days
from tquant.psfactor import PsFactorData
from tquant import BasicData
from tquant import StockData
from kafka import KafkaProducer
from kafka.errors import KafkaError
from web_entry.utils import date_parser

def get_factor_value_by_library_defalt(start_date, end_date, factor_name, library_env='research',
                                Security_list = None, Sort = False):
    start_date, end_date = date_parser(start_date, end_date)
    bd = BasicData()
    date_list = bd.get_trading_day(start_date, end_date)
    tps = PsFactorData()
    df = tps.get_factor_value_by_library(library_env, date_list, [factor_name], security_list=Security_list,
                                         sort=Sort)
    return df