from xquant1.setXquantEnv import xquantEnv
if xquantEnv == 0:
    md_channels = ['168.61.2.35:9243']
elif xquantEnv == 1:
    md_channels = ['168.9.65.23:9243']
else:
    raise Exception("marketdata setGrpcPath error!")