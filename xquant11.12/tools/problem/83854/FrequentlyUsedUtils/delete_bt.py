import os

from xquant.pyfile import Pyfile

py = Pyfile()

# print(len(py.listdir("$21/TradeData")))
# print(len(os.listdir("/app/data/666888/TradeData")))

# # print(py.mkdir("a/b/c"))
# a = [21]
# import pickle
# f=open('sample_pickle.txt','wb')    #以写模式打开二进制文件
# pickle.dump(a, f)


# import pickle
# from xquant.pyfile import Pyfile
# py = Pyfile()
# with py.open("a/tep.pkl", 'wb') as f:
    # data = pickle.dump(a, f)

# with py.open("a/tep.pkl", 'rb') as f:
    # data = pickle.load(f)
    # print(data)

# with open("a/b/c/data.txt", 'wb') as f:
    # pickle.dump(a, f)
 
os.system("rm -rf /app/data/666888/BT_Results/sources/20190530/")
os.system("rm -rf /app/data/666888/BT_Results/results/20190530/")
# os.system("rm -rf /app/data/666888/BT_Trade_OrderCapacity/20190107-20190107/5161101+800")
# print(len(list(py.listdir('output/trade_review_factor_pickle/'))))
# print(len(list(py.listdir('output/production_triggers/5161101+800arb'))))

# os.system("top")

import psutil
import psutil
import os
info = psutil.virtual_memory()
print('内存使用：',psutil.Process(os.getpid()).memory_info().rss)
print('总内存：',info.total)
print('内存占比：',info.percent)
print('cpu个数：',psutil.cpu_count())
print("cup占用率", psutil.cpu_percent())

# from xquant.pyfile import Pyfile
# from System import Codec

# py = Pyfile()
# # "/app/data/666888/AppleData"
# download(self,dstPath,srcPath)
# import time
# print(time.time())
# py.download('/app/data/666888/Temp/factor_pickle', '/output/all_300_500_20170101_20180101_10_all4')
# print(time.time())
# 测试下载功能
# client.download(os.getcwd(),"log.txt")
# # client.download(os.path.join(os.getcwd(),"test"),"test")
# # input("测试完毕请检查文件log.txt和目录test，是否在 %s 目录下" % os.getcwd())
# import os

# # "/app/data/666888/Temp/factor_pickle/AlgoShaolin-000001.SZ-20190109093015-20190110145659.pickle"
# print(os.listdir('/app/data/666888/Temp/factor_pickle/'))

# print(os.path.exists("/app/data/666888/Temp/factor_pickle/AlgoShaolin-000001.SZ-20190109093015-20190110145659.pickle"))

# import pickle
# # outputFactor2, outputSubTag2, tradingUnderlyingCode, factorName = pickle.load(f)
# from xquant.pyfile import Pyfile
# py = Pyfile()
# # with py.open("/app/data/666888/Temp/AlgoShaolin-600030.SH-20190109093015-20190110145659.pickle") as f:
# with open("/app/data/666888/Temp/AlgoShaolin-600030.SH-20190109093015-20190110145659.pickle",'rb') as f:
    # outputFactor = []
    # outputSubTag = []
    # outputFactor2, outputSubTag2, tradingUnderlyingCode, factorName = pickle.load(f)
    
    # # f = open(factorAddress + strategyName)    
    
    # # outputFactor2, outputSubTag2, tradingUnderlyingCode, factorName = Codec.decode(f)    
    # outputFactor.append(outputFactor2)
    # outputSubTag.append(outputSubTag2)
    # print('Use local pickle')
    # print(outputFactor2)
    
# with py.open('output/all_300_500_20170101_20180101_10_all4/.../0000001.sz.pickle', 'rb') as f:
    # pickle.load(f)    
    
    
    
    
    
    
    
    
    
    
    