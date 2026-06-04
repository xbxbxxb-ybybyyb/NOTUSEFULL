import os
import random
import socket
from xquant1.setXquantEnv import xquantEnv
if xquantEnv == 1:
    from .setGrpcPath import md_hash,md_set_channels

class FactorDataPortError(Exception):
    def __init__(self,channelpath):
        self.message = "".join(channelpath) +" grpc server address is not available "
    def __str__(self):
        return self.message

def port_scan(channelpath):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # print(port)
    ip = channelpath.strip().split(":")[0]
    port = int(channelpath.strip().split(":")[1])
    res = sock.connect_ex((ip, port))
    sock.close()
    if res == 0:
        return True
    else:
        return False

def choose_channel(channelpaths):
    nums = len(channelpaths)
    ids = []
    for i in range(len(channelpaths)):
        if port_scan(channelpaths[i]):
            ids.append(i)
            # print(i)
    if len(ids)==0:
        raise FactorDataPortError(channelpaths)
    id = random.randint(0,len(ids)-1)
    return channelpaths[ids[id]]

def choose_channel2():
    maxNums = len(md_hash)
    num = -1
    for i in range(3):
        num = md_hash[ int(random.random()*maxNums)]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        res = sock.connect_ex((md_set_channels[num].get('ip'),md_set_channels[num].get('port')))
        sock.close()
        if res == 0:
            break

    if num == -1:
        raise FactorDataPortError("")
    #channel = f"{md_set_channels[num].get('ip')}:{md_set_channels[num].get('port')}"
    channel = "{0}:{1}".format(md_set_channels[num].get('ip'), md_set_channels[num].get('port'))
    return channel