import json
import unittest

from xquant.factordata import FactorData
from xquant.setXquantEnv import xquantEnv

from kafka import KafkaConsumer

if xquantEnv == 0:
    KAFAKA_CONFIG = "168.61.2.47:9092,168.61.2.48:9092,168.61.2.49:9092"
    #KAFAKA_TOPIC = "cgc_task_log"
    KAFAKA_TOPIC = "XQUANT-STATISTIC-LOG-NOPRD"
elif xquantEnv == 1:
    KAFAKA_CONFIG = "168.9.65.49:9092,168.9.65.50:9092,168.9.65.51:9092,168.9.65.136:9092,168.9.65.137:9092,168.11.225.16:9092,168.11.225.17:9092,168.11.225.18:9092"
    #KAFAKA_TOPIC = "MXSF-AIMAP-TASK-LOG"
    KAFAKA_TOPIC = "XQUANT-STATISTIC-LOG"



class Kafka_consumer():
    '''''
    消费模块: 通过不同groupid消费topic里面的消息
    '''
    def __init__(self, kafkaconfig, kafkatopic, groupid):
        self.kafkaconfig = kafkaconfig
        self.kafkatopic = kafkatopic
        self.groupid = groupid
        self.consumer = KafkaConsumer(self.kafkatopic, group_id = self.groupid,
                                      bootstrap_servers = kafkaconfig )

    def consume_data(self):
        try:
            for message in self.consumer:
                yield message
        except KeyboardInterrupt as e:
            print (e)



class TestStatisticlog(unittest.TestCase):

    def test_demo(self):
        s = FactorData()
        group = 'g'
        consumer = Kafka_consumer(KAFAKA_CONFIG, KAFAKA_TOPIC, group)
        message = consumer.consume_data()
        import time 
        time.sleep(1)
        df1 = s.get_factor_value('Basic_factor', ['000001.SZ'], mddate=['20180808', '20180809'], factor_names=['open', 'high'])
        print(df1.head())
        for msg in message:
            if msg.key.decode().startswith('pycharm'):
                if json.loads(msg.value.decode()).get("tag").startswith('factor_statistic'):
                    print(msg.key.decode())
                    print(msg.value.decode())
                    break
        print("kafka发送成功！")

