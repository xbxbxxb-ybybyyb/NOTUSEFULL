# -*- coding: utf-8 -*-
import time
import grpc
import subprocess
from concurrent import futures

import keepalived_pb2, keepalived_pb2_grpc  # 刚刚生产的两个文件

_day = 60 * 60 * 24 * 7


class KeepalivedService(keepalived_pb2_grpc.KeepalivedServicer):
    def keepalived(self, request, context):
        # max_len = str(len(request.helloworld))
        return keepalived_pb2.HeartBeatResponse(result="")


def main():
    # 多线程服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    # 实例化 计算len的类
    service = KeepalivedService()
    # 注册本地服务,方法ClusterServicer只有这个是变的
    keepalived_pb2_grpc.add_KeepalivedServicer_to_server(service, server)
    # 监听端口
    keepalived_init_port = 9786
    server.add_insecure_port('0.0.0.0:{0}'.format(keepalived_init_port))
    # 开始接收请求进行服务
    server.start()
    # 使用 ctrl+c 可以退出服务
    try:
        while True:
            print("running...")
            time.sleep(_day)
    except KeyboardInterrupt:
        print("stopping...")
        server.stop(0)


if __name__ == '__main__':
    main()
