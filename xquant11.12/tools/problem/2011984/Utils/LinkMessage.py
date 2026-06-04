import json
import requests

corpid = "wwd53282142c96185d"
corpsecret = "Pk0ewu3nuo6JhEaBj_EkuCyiALj0RuISWuZeJcoPdhI"
agentid = 1000033
token_url = " http://168.7.124.15:1080/cgi-bin/gettoken?corpid={0}&corpsecret={1}".format(corpid, corpsecret)
send_url = " http://168.7.124.15:1080/cgi-bin/message/send?access_token={}"


class LinkMessage:
    @staticmethod
    def __get_access_token():
        con = requests.get(token_url)
        json_text = json.loads(con.text)
        access_token = json_text["access_token"]
        return access_token

    def __sendMessage_new(self, user_id, msg):
        access_token = self.__get_access_token()
        post_url = send_url.format(access_token)
        data = {"touser": str(user_id),
                "msgtype": "text",
                "agentid": agentid,
                "text": {
                    "content": msg
                }}
        json_data = json.dumps(data)
        res = requests.post(post_url, json_data)
        if res.status_code != 200:
            raise Exception("消息发送异常！")

    def sendMessage(self, user_id, msg):
        try:
            self.__sendMessage_new(user_id, msg)
        except Exception as e:
            print("新版铃客发送消息失败：{}".format(e))
