import random
import time
import hashlib
from xquant.setXquantEnv import xquantEnv, testEnv
from FactorProvider.conf.DubboConf import get_userid
import requests
import os
import json

nonce0 = [random.randint(0, 15) for i in range(64)]
nonce0 = [hex(i)[2:] for i in nonce0]
nonce = "".join(nonce0)

if xquantEnv == 0:
    # 旧版铃客配置
    eid = "402"
    appid = "402112"
    pubacc = "XT-153e5433-9c76-4b39-b55b-478f5d268788"
    secret = "0f886062348ad60e144c7b98249e5eb4"
    # linkaddr="http://linkxt-test.htsc.com.cn/pubacc/pubsend"
    linkaddr = "http://168.61.13.53:38080/pubacc/pubsend"

    # 新版铃客配置
    corpid = 'ww90dba4dc323845a2'
    corpsecret = 'P9DHuJEBWcWuDRm8Pl9k-RclkMNk955XxzlOc9h__qE'
    agentid = 1000020
    token_url = "http://168.61.113.101:8990/cgi-bin/gettoken?corpid={0}&corpsecret={1}".format(corpid, corpsecret)
    send_url = "http://168.61.113.101:8990/cgi-bin/message/send?access_token={}"

else:
    # 旧版铃客配置
    eid = "402"
    appid = "402758"
    pubacc = "XT-76c0ee6f-17a9-4490-a518-20d4304dc0f2"
    secret = "7686ebf4aeff02b9827d04c5e08ec261"
    linkaddr = "http://168.7.17.9:80/pubacc/pubsend"

    # 新版铃客配置
    corpid = 'wwd53282142c96185d'
    corpsecret = 'Pk0ewu3nuo6JhEaBj_EkuCyiALj0RuISWuZeJcoPdhI'
    agentid = 1000033
    token_url = " http://168.7.124.15:1080/cgi-bin/gettoken?corpid={0}&corpsecret={1}".format(corpid, corpsecret)
    send_url = " http://168.7.124.15:1080/cgi-bin/message/send?access_token={}"


class LinkMessage:
    def __init__(self):
        self.__count_limit_old = 100  # 一次实例化后剩余调用的次数
        self.__count_limit_new = 100  # 一次实例化后剩余调用的次数

    def __sendMessage_old(self, msg):
        if not os.environ.get('ENV_VERSION', False):
            raise Exception("Exception: Spark程序不支持发送铃客消息！")

        t = time.time()
        t = int(t * 10)
        pubtoken = sorted([eid, pubacc, secret, nonce, str(t)])
        pubtoken = "".join(pubtoken)
        pubtoken = hashlib.sha1(pubtoken.encode("utf-8"))
        pubtoken = pubtoken.hexdigest()
        user_id = get_userid()

        json_str = {
            "from": {
                "no": eid,
                "pub": pubacc,
                "nonce": nonce,
                "pubtoken": pubtoken,
                "time": t
            },
            "to": [
                {
                    "no": eid,  # eid
                    "user": [str(user_id)],  # 工号
                    "code": 2
                }
            ],
            "type": 2,
            "msg": {
                "text": msg
            }
        }

        if self.__count_limit_old > 0:
            res = requests.post(linkaddr, json=json_str)
            self.__count_limit_old = self.__count_limit_old - 1
            if res.status_code != 200:
                print("Exception: 旧版铃客发送消息失败：消息发送异常！")
            else:
                print("Info: 旧版铃客消息发送成功！")
        else:
            print("Exception: 旧版铃客发送消息失败：已达到最大发送次数！")

    def __get_access_token(self):
        con = requests.get(token_url)
        json_text = json.loads(con.text)
        access_token = json_text["access_token"]
        return access_token

    def __sendMessage_new(self, msg):
        if not os.environ.get('ENV_VERSION', False):
            raise Exception("Exception: Spark程序不支持发送铃客消息！")
        user_id = get_userid()
        access_token = self.__get_access_token()
        post_url = send_url.format(access_token)
        user_ids = ['015623', '013565']
        for user_id in user_ids:
            data = {"touser": str(user_id),
                    "msgtype": "text",
                    "agentid": agentid,
                    "text": {
                        "content": msg
                    }}
            json_data = json.dumps(data)
            if self.__count_limit_new > 0:
                res = requests.post(post_url, json_data)
                self.__count_limit_new = self.__count_limit_new - 1
                if res.status_code != 200:
                    print("Exception: 新版铃客发送消息失败：消息发送异常！")
                else:
                    print("Info: 新版铃客消息发送成功！")
            else:
                print("Exception: 新版铃客发送消息失败：已达到最大发送次数！")

    def sendMessage(self, msg):
        # try:
        #     self.__sendMessage_old(msg)
        # except Exception as e:
        #     print("旧版铃客发送消息失败：{}".format(e))

        try:
            self.__sendMessage_new(msg)
        except Exception as e:
            print("新版铃客发送消息失败：{}".format(e))

# if __name__ == "__main__":
#     lm = LinkMessage()
#     lm.sendMessage("hahaha!")
