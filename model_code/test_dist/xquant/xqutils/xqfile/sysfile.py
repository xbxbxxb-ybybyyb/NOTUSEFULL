from xquant.setXquantEnv import xquantEnv,testEnv
import requests
from xquant.utils.utils import getKafkaKey,KAFAKA_CONFIG,Kafka_producer
import os
import time
import traceback
import threading

from xquant.xqutils.utils import statisticLog


if xquantEnv == 0:
    FILE_KAFKA_TOPIC = "XQUANT-STORAGE"
    url = "http://168.61.10.212:38033/api/v1/remotefile"
elif xquantEnv == 1:
    FILE_KAFKA_TOPIC = "XQUANT-STORAGE"
    url = "http://168.9.64.62:38033/api/v1/remotefile"
else:
    raise Exception("xquantEnv set error!")


@statisticLog('xqfile',"sysfile")
def strategySendFile(fileLocation):
    try:
        tag = "strategyFile"
        filename = fileLocation.split("/")[-1]
        SendFile(fileLocation,filename,tag)
        return True
    except:
        traceback.print_exc()
        return False
        

@statisticLog('xqfile',"sysfile")
def backtestSendFile(fileLocation):
    try:
        tag = "backTestFile"
        filename = fileLocation.split("/")[-1]
        SendFile(fileLocation,filename,tag)
        return True
    except:
        traceback.print_exc()
        return False


@statisticLog('xqfile',"sysfile")
def SendFile(RelativeLocation,filename,tag):
    new_figLocation = str(time.time()).replace('.', '')+"_"+str(threading.get_ident())
    flag = os.system("cp %s %s" % (RelativeLocation, new_figLocation))
    if flag != 0:
        raise Exception("上传文件失败！请检查目录下是否存在该文件！")

    files = {'file': open(new_figLocation, 'rb')}
    res = requests.post(url, files=files)

    get_file_location = url + "?filename=" + str(new_figLocation)
    res = requests.get(get_file_location)
    if res.status_code != 200:
        os.system("rm %s" % (new_figLocation))
        raise Exception("上传文件失败！")
    value = {"tag": tag, "filename":filename,"location":get_file_location}
    producer = Kafka_producer(FILE_KAFKA_TOPIC)
    producer.sendjsondata(value)
    os.system("rm %s" % (new_figLocation))

