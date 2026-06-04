# _*_ coding:utf-8 _*_
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json

KAFAKA_HOST = "168.6.12.3"
KAFAKA_PORT = 9092
KAFAKA_TOPIC = "XQUANT-FACTOR-DATASYNC"

class Kafka_consumer():
    '''''
    消费模块: 通过不同groupid消费topic里面的消息
    '''

    def __init__(self, kafkahost, kafkaport, kafkatopic, groupid):
        self.kafkaHost = kafkahost
        self.kafkaPort = kafkaport
        self.kafkatopic = kafkatopic
        self.groupid = groupid
        # self.key = key
        self.consumer = KafkaConsumer(self.kafkatopic, group_id = self.groupid,
                bootstrap_servers = '{kafka_host}:{kafka_port}'.format(
                    kafka_host=self.kafkaHost,
                    kafka_port=self.kafkaPort )
                )

    def consume_data(self):
        try:
            for message in self.consumer:
                yield message
        except KeyboardInterrupt as e:
            print (e)


consumer = Kafka_consumer(KAFAKA_HOST, KAFAKA_PORT, KAFAKA_TOPIC, 'id')
message = consumer.consume_data()
for msg in message:
    print(msg)
