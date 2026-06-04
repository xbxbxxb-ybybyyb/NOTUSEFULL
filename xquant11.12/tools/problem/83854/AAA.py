import sys
import os 
import numpy as np
import shutil


# dst_path = "/app/data/666888/test_bt/results/20190708/"
# src_path = "/app/data/666888/BT_Results/results/20190708/"

# shutil.copytree(src_path, dst_path)




print(len(os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-800-production-use-cv-20190429-20190705_20190709-800-300-1200")))
print(len(os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-800-research-use-cv-20190429-20190705_20190709-800-300-1200")))
print(len(os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-big-production-use-cv-20190429-20190705_20190709-big-300-1200")))
print(len(os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-big-research-use-cv-20190429-20190705_20190709-big-300-1200")))


# print(len(os.listdir("/app/data/666888/BT_Results/sources/20190708/bt-20190708-20190708-800-production-use-cv-20190429-20190705_20190708-800-300-1200")))
# print(len(os.listdir("/app/data/666888/BT_Results/sources/20190708/bt-20190708-20190708-800-research-use-cv-20190429-20190705_20190708-800-300-1200")))
# print(len(os.listdir("/app/data/666888/BT_Results/sources/20190708/bt-20190708-20190708-big-production-use-cv-20190429-20190705_20190708-big-300-1200")))
# print(len(os.listdir("/app/data/666888/BT_Results/sources/20190708/bt-20190708-20190708-big-research-use-cv-20190429-20190705_20190708-big-300-1200")))


x = os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-big-production-use-cv-20190429-20190705_20190709-big-300-1200")
y = os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-big-research-use-cv-20190429-20190705_20190709-big-300-1200")
v = os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-800-production-use-cv-20190429-20190705_20190709-800-300-1200")
w = os.listdir("/app/data/666888/BT_Results/sources/20190709/bt-20190709-20190709-800-research-use-cv-20190429-20190705_20190709-800-300-1200")

print(np.array(y)[~np.in1d(y, x)])
print(np.array(y + w)[~np.in1d(y + w, x + v)])

