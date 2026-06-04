"""
根据factordata.proto生成服务框架
factordata_pb2.py  factordata_pb2_grpc.py
生成完后注意修改factordata_pb2_grpc.py里的引用
import xquant.factor.factordata_pb2 as factordata__pb2
"""
from grpc_tools import protoc
"""
factordata.proto
indexTrading.proto
putFactorValue.proto
stockFilter.proto
tansday.proto
hset.proto
"""

protoc.main((
    '',
    '-I.',
    '--python_out=.',
    '--grpc_python_out=.',
    'hset.proto',
))