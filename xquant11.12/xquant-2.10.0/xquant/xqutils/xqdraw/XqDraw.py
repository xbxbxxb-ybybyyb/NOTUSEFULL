from xquant.setXquantEnv import xquantEnv,testEnv
import sys
import json
import requests
import os
import time

from xquant.pydraw import pydraw_Kafka_producer,IMAGE_KAFKA_TOPIC

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

        if xquantEnv == 1:
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