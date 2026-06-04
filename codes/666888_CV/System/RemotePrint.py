import os
import grpc
import pickle
from Rpc import RpcService_pb2_grpc
from Rpc.RpcService_pb2 import PrintRequest

isExecutor = False

# 通过环境变量确定该python进程是在Driver还是在Executor
if 'RPC_DRIVER_HOST' in os.environ and 'RPC_DRIVER_PORT' in os.environ:
    isExecutor = True

if isExecutor:
    rpcAddr = '{}:{}'.format(os.environ['RPC_DRIVER_HOST'], os.environ['RPC_DRIVER_PORT'])
    rpcChannel = grpc.insecure_channel(rpcAddr)
    rpcStub = RpcService_pb2_grpc.QuantFactorStub(rpcChannel)


def print(*args, **kwargs):
    """
    该函数用于在Executor端进行打印，其打印结果会通过RPC传到Driver并显示到终端
    """
    if not isExecutor:
        raise Exception('The remote print() can only be called in the Executor')
    dump = pickle.dumps(args)
    request = PrintRequest(pickledArgs=dump)
    rpcStub.remotePrint(request)
