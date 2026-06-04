# -*- coding: utf-8 -*-
import pickle
from Rpc import RpcService_pb2_grpc
from Rpc.RpcService_pb2 import Empty


class QuantFactorServicer(RpcService_pb2_grpc.QuantFactorServicer):
    """
    接受来自Executor的print请求，并在Driver终端打印
    """
    def remotePrint(self, request, context):
        args = pickle.loads(request.pickledArgs)
        # 在开头换行, 避免和Spark的进度条冲突
        print('\n', *args)
        empty = Empty()
        return empty
