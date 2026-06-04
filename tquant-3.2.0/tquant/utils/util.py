import os
import json
import ray
from tquant.conf.DubboConf import get_jurisdictionData
from kafka import KafkaProducer
from kafka.errors import KafkaError

jurisdictionData_dict = {}


def __set_jurisdictionData():
    c_name = "jurisdictionData"
    global jurisdictionData_dict
    if not jurisdictionData_dict.get(c_name):
        jurisdictionData_dict[c_name] = get_jurisdictionData()


def get_factors_info():
    __set_jurisdictionData()
    data = jurisdictionData_dict["jurisdictionData"]
    Basic_factordata = data["因子信息"]["jurisdictionData"]["Basic_factordata"]
    cata_name_dict = {'行情指标': 'market', '估值指标': 'valuation', '财务分析': 'financialanalysis',
                      '财务报表': 'financialreport', '风险分析': 'riskanalysis'}
    # 元数据目录id有新增或变动时需更改
    catalog_id_dict = {2: 'market', 3: 'valuation', 4: 'financialreport', 5: 'dividendindex', 6: 'newmsgindex',
                       7: 'conforecastindex', 8: 'financialanalysis', 9: 'riskanalysis', 10: 'alpha',
                       11: 'barra', 12: 'technicalanalysis', 13: 'momentum', 14: 'emotion'}
    factorInfo = Basic_factordata["factorInfo"]
    factors_info = {}
    for f in factorInfo:
        catalog_name = catalog_id_dict.get(factorInfo[f]["idInfo"][-2])
        if not catalog_name:
            continue
        if not factors_info.get(catalog_name):
            factors_info[catalog_name] = [f]
        else:
            factors_info[catalog_name].append(f)
    return factors_info


def get_factor_table(factor_list):
    __set_jurisdictionData()
    data = jurisdictionData_dict["jurisdictionData"]
    Basic_factordata = data["因子信息"]["jurisdictionData"]["Basic_factordata"]
    factorInfo = Basic_factordata["factorInfo"]
    f_table = {}
    for f in factorInfo.keys():
        if f in factor_list:
            if not f_table.get(factorInfo[f]['table']):
                f_table[factorInfo[f]['table']] = [f]
            else:
                f_table[factorInfo[f]['table']].append(f)
    return f_table


def upload_pdf(file_path):
    file_path


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
    def __init__(self, scene='backtest'):
        self.bootstrap_servers = ''
        self.kafkatopic = ''
        self.__get_kafka_config(scene)
        self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

    def __get_kafka_config(self, scene):
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
