from xquant.setXquantEnv import xquantEnv,testEnv
import sys
import json
import requests
from xquant.utils.utils import getKafkaKey,KAFAKA_CONFIG
import os
import time

try:
    from kafka import KafkaProducer
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except:
    pass

if xquantEnv == 0:
    IMAGE_KAFKA_TOPIC = "cgc_task_log"
elif xquantEnv == 1:
    IMAGE_KAFKA_TOPIC = "MXSF-AIMAP-XQUANT-LOG"
else:
    raise Exception("xquantEnv set error!")


def pydraw_singleton(Kafka_producer):
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

@pydraw_singleton
class pydraw_Kafka_producer():
    """
    生产模块：根据不同的key，区分消息
    """
    def __init__(self,topic):
        self.kafkatopic = topic
        self.key = getKafkaKey()
        if not self.key:
            raise Exception("获取kafka key 失败！")
        bootstrap_servers = KAFAKA_CONFIG
        self.producer = KafkaProducer(bootstrap_servers = bootstrap_servers)

    def sendjsondata(self, params):
        try:
            parmas_message = json.dumps(params,ensure_ascii=False)
            producer = self.producer
            v = parmas_message.encode('utf-8')
            k = self.key.encode('utf-8')
            producer.send(self.kafkatopic, key=k, value= v)
            producer.flush()
        except KafkaError as e:
            print(e)


def showfig(figLocation):
    """ 指示画图位置
    :param figLocation:位置
    :return:
    """
    if os.environ.get('BIG_DATA_PREPATH', False):
        print("draw image,-D%s" % (figLocation))
    else:
        permission_end = ['zip','rar','RAR','png','jpg','JPG','PNG','gif','GIF']
        file_end = figLocation.split(".")[-1]
        if file_end not in permission_end:
            raise Exception("文件命名格式错误，目前支持格式：压缩包类（'zip','rar','RAR'），图片类（'png','jpg','JPG','PNG','gif','GIF'）")
        name_end = str(int(time.time())) + "."
        new_figLocation = figLocation.split(".")[0] + name_end + figLocation.split(".")[0 - 1]
        os.system("mv %s %s" % (figLocation, new_figLocation))
        if xquantEnv == 0:
            url = "http://168.61.10.212:38033/api/v1/remotefile"
            files = {'file': open(new_figLocation, 'rb')}
            res = requests.post(url, files=files)

            res = requests.get(url + "?filename=" + str(new_figLocation))
            if res.status_code != 200:
                raise Exception("上传图片失败！")
            value = {"tag": "image","message": "$image," + new_figLocation}

        elif xquantEnv == 1:
            url = "http://168.9.64.62:38033/api/v1/remotefile"
            files = {'file': open(new_figLocation, 'rb')}
            res = requests.post(url, files=files)

            res = requests.get(url + "?filename=" + str(new_figLocation))
            if res.status_code != 200:
                raise Exception("上传图片失败！")
            value = {"tag": "image", "message": "$image," + new_figLocation}
        else:
            raise Exception("xquantEnv set error!")
        producer = pydraw_Kafka_producer(IMAGE_KAFKA_TOPIC)
        producer.sendjsondata(value)