import random
import time
import hashlib
from xquant.setXquantEnv import xquantEnv,testEnv
from xquant.xqutils.utils import get_userid
import requests
import os

nonce0 = [random.randint(0,15) for i in range(64)]
nonce0 = [hex(i)[2:] for i in nonce0]
nonce = "".join(nonce0)

if xquantEnv == 0:
    eid="402"
    appid="402112"
    pubacc="XT-153e5433-9c76-4b39-b55b-478f5d268788"
    secret="0f886062348ad60e144c7b98249e5eb4"
    #linkaddr="http://linkxt-test.htsc.com.cn/pubacc/pubsend"
    linkaddr="http://168.61.13.53:38080/pubacc/pubsend"
else:
    eid = "402"
    appid = "402758"
    pubacc="XT-76c0ee6f-17a9-4490-a518-20d4304dc0f2"
    secret = "7686ebf4aeff02b9827d04c5e08ec261"
    linkaddr = "http://168.7.17.9:80/pubacc/pubsend"

class LinkMessage:
    def __init__(self):
        self.__count_limit = 5#一次实例化后剩余调用的次数

    def sendMessage(self, msg):
        if not os.environ.get('ENV_VERSION', False):
            raise Exception("Exception: Spark程序不支持发送铃客消息！")

        t = time.time()
        t = int(t*10)
        pubtoken = sorted([eid,pubacc,secret,nonce,str(t)])
        pubtoken = "".join(pubtoken)
        pubtoken = hashlib.sha1(pubtoken.encode("utf-8"))
        pubtoken = pubtoken.hexdigest()
        user_id = get_userid()

        json_str = {
            "from": {
                    "no": eid,
                    "pub": pubacc,
                    "nonce":nonce,
                    "pubtoken":pubtoken,
                    "time":t
                },
            "to": [
                {
                    "no": eid,#eid
                    "user": [str(user_id)],#工号
                    "code":2
                }
            ],
            "type":2,
            "msg": {
                "text": msg
            }
        }

        if self.__count_limit > 0 :
            res =requests.post(linkaddr, json = json_str)
            self.__count_limit = self.__count_limit-1
            if res.status_code != 200:
                print("Exception: 发送铃客消息失败：消息发送异常！")
            else:
                print("Info: 铃客消息发送成功！")
        else:
            print("Exception: 发送铃客消息失败：已达到最大发送次数！")


if __name__=="__main__":
    lm = LinkMessage()
    lm.sendMessage("hahaha!")