import json
import os

import requests
from loguru import logger
from xquant.setXquantEnv import xquantEnv, testEnv

# 接收信息的用户列表
user_ids = [
    '013150', # 沈俊灵
    '022917', # 刘晔闻
    # '012872',  # 胡俊鹏
    # '015612',  # 陈俊男
#    '018083',  # 郭晨
    '019073',  # 张博文
    # '015518',  # 陈家强
]

if xquantEnv == 0:
    # 新版铃客配置
    corpid = 'ww90dba4dc323845a2'
    corpsecret = 'P9DHuJEBWcWuDRm8Pl9k-RclkMNk955XxzlOc9h__qE'
    agentid = 1000020
    token_url = "http://168.61.113.101:8990/cgi-bin/gettoken?corpid={0}&corpsecret={1}".format(corpid, corpsecret)
    send_url = "http://168.61.113.101:8990/cgi-bin/message/send?access_token={}"
else:
    # 新版铃客配置
    corpid = 'wwd53282142c96185d'
    corpsecret = 'Pk0ewu3nuo6JhEaBj_EkuPS_A0-ku8KHi6fsSbsCipk'
    agentid = 1000033
    token_url = " http://168.9.11.148:1080/cgi-bin/gettoken?corpid={0}&corpsecret={1}".format(corpid, corpsecret)
    send_url = " http://168.9.11.148:1080/cgi-bin/message/send?access_token={}"


class LinkMessage:
    def __init__(self):
        self.__count_limit_new = 200  # 一次实例化后剩余调用的次数

    @staticmethod
    def __get_access_token():
        con = requests.get(token_url)
        json_text = json.loads(con.text)
        access_token = json_text["access_token"]
        return access_token

    def __sendMessage_new(self, msg):
        if not os.environ.get('ENV_VERSION', False):
            raise Exception("Exception: Spark程序不支持发送铃客消息！")
        access_token = self.__get_access_token()
        post_url = send_url.format(access_token)

        success_user_ids = []

        for user_id in user_ids:
            data = {"touser": user_id,
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
                    logger.error("Exception: 铃客发送消息失败：消息发送异常！")
                else:
                    success_user_ids.append(user_id)
            else:
                logger.error("Exception: 铃客发送消息失败：已达到最大发送次数！")
        if len(success_user_ids) != len(user_ids):
            logger.error(
                "铃客漏发消息：expect_user_list={}, actual_user_list={}, msg={}".format(user_ids, success_user_ids, msg))
        else:
            logger.info(
                "铃客成功发送消息：msg={}, users={}".format(msg, success_user_ids))

    def sendMessage(self, msg):
        try:
            self.__sendMessage_new(msg)
        except Exception as e:
            logger.error("铃客发送消息失败：msg={}, e={}".format(msg, e))


class FormatMsg:
    def __init__(self, task_name="任务名称", start_file="test.py"):
        self.task_name = task_name
        self.start_file = start_file
        self.lm = LinkMessage()

        task_dict = {"数据下载-金工基础H5": "8890", "因子更新-DayFactor": "10482",
                     "因子更新-FixFactor": "10482", "因子更新-DayFactor(第一批)": "10482",
                     "数据更新-Wind晚间barra": "10482", "数据更新-Wind晚间源表": "10482",
                     "数据更新-Wind晚间加工表": "10482", "高频alpha-增强分钟": "10482",
                     "因子更新-JGFactor": "10482", "因子更新-SuntimeFactor": "10482",
                     "数据更新-Wind-凌晨": "10482", "数据更新-Suntime": "10482",
                     "数据更新-Suntime-新": "10482", "数据下载-FndSecportfolio": "10482",
                     "巡检-Factor": "10482", "备份-Factor": "10482",
                     "备份基础数据": "10482", "高频alpha-指数权重": "9406",
                     "数据校验-指数权重": "10866", "数据下载-GOGOAL2更新": "10482",
                     "数据更新-Wind晚间Universe": "10482",}
        self.task_no = task_dict.get(task_name, "999999")



    def sendMessage(self, msg):
        info_msg = self.task_name + "_" + self.task_no + "_" + self.start_file + "_" + msg
        print(info_msg)
        self.lm.sendMessage(info_msg)






if __name__ == "__main__":
    lm = FormatMsg("数据校验-指数权重", "link.py")
    lm.sendMessage("铃客消息测试!")
