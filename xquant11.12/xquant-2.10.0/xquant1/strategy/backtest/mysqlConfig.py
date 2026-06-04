from xquant1.setXquantEnv import xquantEnv,testEnv

if xquantEnv == 0:
    if testEnv == 40:
        host = '168.61.2.14'
        user = 'xquant_uct'
        password = 'xquant'
        db = 'xquant_uct'
        port = 3312
    elif testEnv == 63:
        host = '168.61.2.14'
        user = 'xquant_sit'
        password = 'xquant'
        db = 'xquant_sit'
        port = 3310
elif xquantEnv ==1:
    host = '168.9.65.8'
    user = 'xquant'
    password = 'xquant9527'
    db = 'xquant'
    port = 3307
else:
    raise Exception("backtest mysqlConfig 设置错误！")