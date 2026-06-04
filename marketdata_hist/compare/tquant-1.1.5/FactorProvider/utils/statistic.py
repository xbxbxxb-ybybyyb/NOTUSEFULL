import os
import json
from FactorProvider.setEnv import xquantEnv, sysFlag

try:
    from kafka import KafkaProducer
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except:
    pass


def getKafkaKey():
    XQUANT_CONF_FILE = os.environ['XQUANT_CONF_FILE']
    # XQUANT_CONF_FILE = "/tmp/python/xquant_conf"
    with open(XQUANT_CONF_FILE, 'r') as f:
        r = f.readlines()
        for line in r:
            if line.startswith("logkeyPrefix"):
                return line.strip().split("=")[-1].strip()


if xquantEnv == 0:
    KAFAKA_CONFIG = "168.61.2.47:9092,168.61.2.48:9092,168.61.2.49:9092"
    # KAFKA_TOPIC = "cgc_task_log"
    KAFKA_TOPIC = "XQUANT-STATISTIC-LOG-NOPRD"
elif xquantEnv == 1:
    KAFAKA_CONFIG = "168.9.65.49:9092,168.9.65.50:9092,168.9.65.51:9092,168.9.65.136:9092,168.9.65.137:9092,168.11.225.16:9092,168.11.225.17:9092,168.11.225.18:9092"
    # KAFKA_TOPIC = "MXSF-AIMAP-TASK-LOG"
    KAFKA_TOPIC = "XQUANT-STATISTIC-LOG"


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
    '''''
    生产模块：根据不同的key，区分消息
    '''

    def __init__(self, topic):
        self.kafkatopic = topic
        self.key = getKafkaKey()
        if not self.key:
            raise Exception("获取kafka key 失败！")
        bootstrap_servers = KAFAKA_CONFIG
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    def sendjsondata(self, params):
        try:
            parmas_message = json.dumps(params, ensure_ascii=False)
            producer = self.producer
            v = parmas_message.encode('utf-8')
            k = self.key.encode('utf-8')
            producer.send(self.kafkatopic, key=k, value=v)
            producer.flush()
        except KafkaError as e:
            print(e)


def statisticLog(module: str = '', genus: str = ''):
    """
    监控日志装饰器
    :return:
    :param module:  类型如下
            bigdata	大数据文件操作
            marketdata	高频行情访问模块
            tensorflow	tensorflow库操作
            factordata	量化因子访问模块
    :param genus:   所属类名
    :return:
    """

    def printStar(func):
        def _call(*args, **kw):
            # 日志输出
            # $statistic - log：为固定的埋点开始标识
            # module：为埋点模块名称（必填）
            # submodule：为埋点子模块名称（可选）
            # subject：为操作类型（可选）
            # platform：为平台标识（必填），预定义值见下文
            subject = func.__name__
            if len(genus) > 0:
                subject = genus + "." + subject
            if sysFlag == 'big_data':
                print("$statistic-log,module=%s,subject=%s,platform=XQUANT-Cloud" % (module, subject))
            else:
                try:
                    # value = {"tag": "statistic", "message":"$statistic-log,module=%s,subject=%s,platform=XQUANT-Cloud" % (module,subject)}
                    value = {
                        "tag": "statistic",
                        "message": {
                            "module": module,
                            "subject": subject,
                            "platform": "XQUANT-Cloud"
                        }
                    }
                    producer = Kafka_producer(KAFKA_TOPIC)
                    producer.sendjsondata(value)
                except:
                    pass
            return func(*args, **kw)

        return _call

    return printStar
