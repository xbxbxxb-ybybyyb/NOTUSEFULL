# -*- coding: utf-8 -*-
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json


KAFAKA_HOST = "168.6.12.3"
KAFAKA_PORT = 9092
KAFAKA_TOPIC = "XQUANT-FACTOR-DATASYNC"

class Kafka_producer():
    '''
    使用kafka的生产模块
    '''

    def __init__(self, kafkahost,kafkaport, kafkatopic):
        self.kafkaHost = kafkahost
        self.kafkaPort = kafkaport
        self.kafkatopic = kafkatopic
        self.producer = KafkaProducer(bootstrap_servers = '{kafka_host}:{kafka_port}'.format(
            kafka_host=self.kafkaHost,
            kafka_port=self.kafkaPort
            ))

    def sendjsondata(self, params):
        try:
            parmas_message = json.dumps(params)
            producer = self.producer
            producer.send(self.kafkatopic,parmas_message.encode('utf-8'))
            producer.flush()
        except KafkaError as e:
            print(e)
def push_data(params):
    producer = Kafka_producer(KAFAKA_HOST,KAFAKA_PORT,KAFAKA_TOPIC)
    producer.sendjsondata(params)





