import calendar
import pandas as pd
import datetime as dt
import os
import json
from SmartFactor.calculation.DataCalculation import run_factors_days, run_securities_days
# from SmartFactor.FactorCalc import run_factors_days, run_securities_days
from tquant.psfactor import PsFactorData
from tquant import BasicData
from tquant import StockData
from kafka import KafkaProducer
from kafka.errors import KafkaError


def web_calculation(
        factor_name,
        origin_start_date,
        origin_end_date,
        file_path,
        calc_env='release',
        mode='show',
        factor_type=None,
        dynamic_load_attr=True,
):
    """
    :param factor_name: 因子名
    :param origin_start_date: 起始时间,接受 YYMMDD YY/MM/DD YY/MM
    :param origin_end_date: 结束时间,接受 YYMMDD YY/MM/DD YY/MM
    :param file_path: 文件地址
    :param calc_env: 计算环境,默认release
    :param mode: 计算模式,默认show
    :param factor_type: 因子类型,day或tick
    :param dynamic_load_attr: 是否动态加载因子属性,默认为True
    :return:
    """
    library_name = None
    if factor_type:
        factor_type = factor_type.lower()
    else:
        psfactor = PsFactorData()
        library_name = psfactor.get_library_name_by_factor(factor_name, calc_env)
        if 'DAY' in library_name:
            factor_type = 'day'
        elif 'TICK' in library_name:
            factor_type = 'tick'
        else:
            raise Exception('库名{}中不包含TICK或DAY'.format(library_name))

    num_cpus = 1
    object_store_memory = None



    if '/' not in origin_start_date and '/' not in origin_end_date:
        start_date = origin_start_date
        end_date = origin_end_date
    else:
        if origin_start_date.count('/') == 2:
            start_date = origin_start_date.replace('/', '')
        else:
            origin_start_date = origin_start_date.split('/')
            start_date = '{}{}{}'.format(origin_start_date[0], origin_start_date[1],
                                         '01')
        if origin_end_date.count('/') == 2:
            end_date = origin_end_date.replace('/', '')
        elif origin_end_date == 'td':
            end_date = dt.datetime.now().strftime("%Y%m%d")
        else:
            origin_end_date = origin_end_date.split('/')
            last_day_of_month = str(
                calendar.monthrange(int(origin_end_date[0]), int(origin_end_date[1]))[
                    1])
            end_date = '{}{}{}'.format(origin_end_date[0], origin_end_date[1],
                                       last_day_of_month)
    if factor_type == 'day':
        result = run_factors_days(
                [factor_name], start_date, end_date,
                return_mode=mode, library_env=calc_env,
                file_path=file_path, check_olddata=True,
                allow_merge_olddata=True, dynamic_load_attr=dynamic_load_attr
                # library_name=library_name,
            )
    elif factor_type == 'tick':
        result = run_securities_days(
                [factor_name], start_date, end_date,
                 return_mode=mode, library_env=calc_env, file_path=file_path,
                 check_olddata=True, dynamic_load_attr=dynamic_load_attr
                 # library_name=library_name,
             )
    else:
        raise Exception('因子类型不在day和tick中:{}'.format(factor_type))

    return result


def get_psfactor_data(start_date, end_date, factor_name, library_type='research'):
    sd = StockData()
    bd = BasicData()
    tps = PsFactorData()
    tradingdate = bd.get_trading_day(end_date, -5)[-1]
    stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
    date_list = bd.get_trading_day(start_date, end_date)
    # 个人因子
    library_name = tps.get_library_name_by_factor(factor_name, library_type)
    factor_data = tps.get_factor_value(library_name, date_list, [factor_name], stock_list)[
        factor_name]
    factor_data.index = pd.DatetimeIndex(factor_data.index)
    return factor_data

def get_factor_value_by_library_defalt(start_date, end_date, factor_name, library_env='research',
                                Security_list = None, Sort = False):
    start_date, end_date = date_parser(start_date, end_date)
    bd = BasicData()
    date_list = bd.get_trading_day(start_date, end_date)
    tps = PsFactorData()
    df = tps.get_factor_value_by_library(library_env, date_list, [factor_name], security_list=Security_list,
                                         sort=Sort)
    return df


def date_parser(sdate, edate):
    try:
        dt.datetime.strptime(sdate, '%Y/%m')
        origin_start_date = sdate.split('/')
        start_date = '{}{}{}'.format(origin_start_date[0], origin_start_date[1], '01')
    except:
        start_date = sdate
    try:
        dt.datetime.strptime(edate, '%Y/%m')
        origin_end_date = edate.split('/')
        last_day_of_month = str(calendar.monthrange(int(origin_end_date[0]), int(origin_end_date[1]))[1])
        end_date = '{}{}{}'.format(origin_end_date[0], origin_end_date[1], last_day_of_month)
    except:
        end_date = edate

    return start_date, end_date

def trans_enddate(end_date):
    if not isinstance(end_date, str):
        end_date = str(end_date)
    if end_date.lower() == 'td':
        now_time = dt.datetime.now()
        if int(now_time.hour) < 20:
            end_date = (dt.datetime.now()- dt.timedelta(1)).strftime('%Y/%m/%d')
        else:
            end_date = dt.datetime.now().strftime('%Y/%m/%d')
    return end_date


def kafka_singleton(Kafka_producer):
    # instance_mark是除了进程id之外，单例的标志符
    _instance = {}

    def inner(*args, **kargs):
        if kargs.get("topic"):
            # 判断哪个参数字段作为标志符
            instance_mark = kargs["topic"]
        else:
            instance_mark = args[0]
        if (os.getpid(), instance_mark) not in _instance:
            _instance[(os.getpid(), instance_mark)] = Kafka_producer(*args, **kargs)
        return _instance[(os.getpid(), instance_mark)]

    return inner


@kafka_singleton
class Kafka_producer():
    def __init__(self, scene='backtest', servers='', topic=''):
        self.bootstrap_servers = servers
        self.kafkatopic = topic
        self.__get_kafka_config(scene)
        self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

    def __get_kafka_config(self, scene):
        if self.bootstrap_servers or self.kafkatopic:
            if not self.bootstrap_servers:
                raise Exception('当topic存在时请填写servers参数')
            if not self.kafkatopic:
                raise Exception('当services存在时请填写topic参数')
        else:
            exec_env = os.environ.get('exec_env')
            if not exec_env:
                raise Exception("未获取到exec_env")
            exec_env = exec_env.lower()
            if exec_env not in ['dev-prd', 'dev-uat', 'sit-prd', 'sit-uat', 'uat', 'prd']:
                raise Exception(
                    '环境变量exec_env不在dev-prd,dev-uat,sit-prd,sit-uat,uat,prd中: {}'.format(exec_env))
            if scene not in ['test', 'calc', 'backtest', 'trace']:
                raise Exception('scene必须在test,calc,backtest,trace中')
            if exec_env in ['dev-prd', 'dev-uat', 'sit-prd', 'sit-uat']:
                self.bootstrap_servers = '168.61.2.47:9092,168.61.2.48:9092,168.61.2.49:9092'
            elif exec_env == 'uat':
                self.bootstrap_servers = '168.63.117.24:9092,168.63.117.25:9092,168.63.117.26:9092'
            elif exec_env == 'prd':
                self.bootstrap_servers = '168.9.65.49:9092,168.9.65.50:9092,168.9.65.51:9092,' \
                                         '168.9.65.136:9092,168.9.65.137:9092,' \
                                         '168.11.225.16:9092,168.11.225.17:9092,168.11.225.18:9092,' \
                                         '168.11.225.93:9092,168.11.225.94:9092,168.11.225.95:9092,' \
                                         '168.11.225.79:9092,168.11.225.80:9092,' \
                                         '168.11.224.31:9092,168.11.224.32:9092,168.11.225.104:9092'
            if scene == 'backtest':
                if exec_env == 'dev-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-BACKTEST-DEV-PRD'
                elif exec_env == 'dev-uat':
                    self.kafkatopic = 'TQUANT-FACTOR-BACKTEST-DEV-UAT'
                elif exec_env == 'sit-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-BACKTEST-SIT-PRD'
                elif exec_env == 'sit-uat':
                    self.kafkatopic = 'TQUANT-FACTOR-BACKTEST-SIT-UAT'
                elif exec_env == 'uat':
                    self.kafkatopic = 'TQUANT-FACTOR-BACKTEST-UAT'
                elif exec_env == 'prd':
                    self.kafkatopic = 'TQUANT-FACTOR-BACKTEST'
            elif scene == 'calc':
                if exec_env == 'dev-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-CALC-DEV'
                elif exec_env == 'sit-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-CALC-SIT'
                elif exec_env == 'prd':
                    self.kafkatopic = 'TQUANT-FACTOR-CALC'
            elif scene == 'trace':
                if exec_env == 'dev-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-TRACE-DEV'
                elif exec_env == 'sit-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-TRACE-SIT'
                elif exec_env == 'prd':
                    self.kafkatopic = 'TQUANT-FACTOR-TRACE'
            elif scene == 'test':
                if exec_env == 'dev-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-TEST-DEV'
                elif exec_env == 'sit-prd':
                    self.kafkatopic = 'TQUANT-FACTOR-TEST-SIT'
                elif exec_env == 'prd':
                    self.kafkatopic = 'TQUANT-FACTOR-TEST'

    def send_json_data(self, params):
        try:
            parmas_message = json.dumps(params, ensure_ascii=False)
            producer = self.producer
            v = parmas_message.encode('utf-8')
            producer.send(self.kafkatopic, value=v)
            producer.flush()
        except KafkaError as e:
            print(e)

