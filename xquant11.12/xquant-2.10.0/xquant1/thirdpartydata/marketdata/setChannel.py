import os
import random
import socket


class MarketDataPortError(Exception):
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
        raise MarketDataPortError(channelpaths)

    id = random.randint(0,len(ids)-1)
    return channelpaths[ids[id]]