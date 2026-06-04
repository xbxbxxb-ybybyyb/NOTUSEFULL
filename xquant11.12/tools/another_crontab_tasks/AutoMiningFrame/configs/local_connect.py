import os
import json
from AutoMiningFrame.FactorAutoMining.utils.setenv import get_env


def parse_connect():
    connect_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"connections.json")
    with open(connect_config_path, "r") as f:
        connect_info_dict = json.load(f)
        env = get_env()
        connect_info = connect_info_dict[env]
        ip = connect_info["ip"]
        user = connect_info['user']
        passsword = connect_info['passwd']
    port_string = os.popen("ps -ef|grep tcp-pf|grep 8889|awk '{print $14}'|awk -F ':' '{print $2}'|head -1").read().strip()
    port_string = port_string if port_string else "8848"
    port = int(port_string)
    return ip, port, user, passsword
