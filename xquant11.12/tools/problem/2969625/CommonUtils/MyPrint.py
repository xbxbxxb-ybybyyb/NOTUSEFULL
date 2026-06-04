import os
from xquant.compute.sparkmr import remote_print


def myPrint(*args):
    isExecutor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ
    if isExecutor:
        remote_print(*args)
    else:
        print(*args)
