import os
import datetime

def showTime():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return now
    
def myPrint(strings, log_file="logs.txt"):
    # log_file: saved_nn文件夹下的相对路径
    print(strings)
    log_file = os.path.join("/data/user/000053/quanttest/saved_nn/logs", log_file)
    with open(log_file, 'a', encoding='utf-8') as f:
        print(strings, file=f)