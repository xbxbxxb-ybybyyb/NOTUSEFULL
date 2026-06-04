# coding=utf-8
import json
import os
import atexit
import signal
import traceback

import pymysql

import re
import requests
import datetime
import sys
import time
import warnings
from xquant1.utils import statisticLog
import string
import random

warnings.filterwarnings("ignore")

global id_lis
id_lis = []
global tableName
tableName = 'application'
global databaseIp
databaseIp = []
global databaseName
databaseName = []
global pycharm_group

class tf():
    # 根据实际传入
    @statisticLog("tensorflow")
    def __init__(self):
        pass

    @statisticLog("tensorflow")
    def get(self):
        return


def term_sig_handler(signum, frame):
    # print('catched singal: %d' % signum)
    if id_lis:
        db = pymysql.connect(databaseIp[0], "xquant_tyjk", "X7_mJw12m8UW", databaseName[0])
        cursor = db.cursor()
        sql = "update application set status = 999 where status in (0,1,3,6) and id in %s" % str(id_lis)
        sql = sql.replace('[', '(')
        sql = sql.replace(']', ')')
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
    sys.exit()


def runTasks(filename, param):
    t = tf()
    t.get()

    signal.signal(signal.SIGTERM, term_sig_handler)
    signal.signal(signal.SIGINT, term_sig_handler)

    params = json.loads(param)

    envtype = os.getenv("ENV_VERSION")
    if envtype == 'sit':
        databaseIp.append("168.63.17.19")
        databaseName.append("tyjk_sit")
        uploadIp = "168.61.10.212"
        cpuimage = "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:v3.0"
        gpuimage = "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:uat_v3.0"
    elif envtype == 'uat':
        databaseIp.append("168.63.17.19")
        databaseName.append("tyjk_server")
        uploadIp = "168.61.10.212"
        cpuimage = "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:uat_v3.0"
        gpuimage = "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:uat_v3.0"
    elif envtype == 'prd':
        databaseIp.append("168.11.1.5")
        databaseName.append("xquant_tyjk")
        uploadIp = "168.9.64.62"
        cpuimage = "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_v3.0"
        gpuimage = "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0"
    db = pymysql.connect(databaseIp[0], "xquant_tyjk", "X7_mJw12m8UW", databaseName[0],charset="utf8")
    cursor = db.cursor()    
    cursor.execute('SET CHARACTER SET utf8;')
    # is_sync = params["is_sync"]
    parallel_list = params["parallel_list"]

    # f = open("/tmp/xquant_conf","r")

    filepath = os.getenv('XQUANT_CONF_FILE')
    f = open(filepath, "r")
    file = f.read()
    f.close()
    file = file.split('\n')

    entryFileName = filename
    xquant_id = file[2].split('=')[1]

    log_keyprefix = file[3].split('=')[1]
    log_key = log_keyprefix.split('_')[-1]
    task_type = log_keyprefix.split('_')[0]
    user_id = file[4].split('=')[1]
    if log_key == "son":
        print("error : Subtask cannot call AIMR")
        cursor.close()
        db.close()
    else:
        cursor.execute(
            "select job_id,rw_path_set,ro_path_set,resource_config from {} where xquant_id={} limit 1".format(tableName,
                                                                                                              xquant_id))
        data = cursor.fetchone()
        fjob_id = data[0]
        rw_path_set = data[1]
        ro_path_set = data[2]
        group = json.loads(data[3])["group"]
        appid = json.loads(data[3])["appid"]
        if 'docker_version' not in params.keys():
            gpu = params['gpu']
            if int(gpu) > 0:
                image = gpuimage
            else:
                image = cpuimage
        else:
            image = params['docker_version']
        if 'preferred_gpu' not in params.keys():
            preferred_gpu=0
        else:
            preferred_gpu=params['preferred_gpu']
        if preferred_gpu not in [0,1]:
            print('please input right preferred_gpu!')
            sys.exit()
        if task_type == 'xquant':
            log_keyprefix = log_keyprefix
            entryFilePath = file[0].split('=')[1]
            cursor.execute("select count(1) from {} where xquant_id={}".format(tableName,xquant_id))
            count = cursor.fetchone()[0]
            if count >1:
                print('"error : Subtask cannot call AIMR"')
                sys.exit()
            resource_config_ = {"entryFilePath": entryFilePath,
                                "entryFileName": entryFileName,
                                "memory": params['memory'],
                                "cpu": params['cpu'],
                                "tag": "XQuant Common Task",
                                "image":image,
                                "preferred_gpu":preferred_gpu,
                                "gpu": params['gpu'],
                                "group": group,
                                "taskParam": '',
                                "appid":appid
                                }
        else:
            log_keyprefix = log_keyprefix + "_son"
            nowTime = (datetime.datetime.now()).strftime('%Y%m%d%H%M%S')
            pwd = os.popen("pwd").read().split()[0]
            tarName = "%s_%s.tar" % (xquant_id, nowTime)
            os.system("mkdir -p /tmp/%s/xquant && cd %s && cp -r * /tmp/%s/xquant" % (nowTime, pwd, nowTime))
            os.system("cd /tmp/%s && tar -cf %s xquant" % (nowTime, tarName))
            url = "http://%s:38033/api/v1/remotefile" % uploadIp
            files = {'file': open("/tmp/%s/%s" % (nowTime, tarName), 'rb')}
            res = requests.post(url, files=files)
            entryFilePath = "/tmp/%s" % xquant_id
            os.system("cd /tmp && rm -rf %s" % (nowTime))
            pycharm_group = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            pycharm_group=str(xquant_id)+"_"+pycharm_group
            resource_config_ = {"entryFilePath": entryFilePath,
                                "entryFileName": entryFileName,
                                "packageFileName": tarName,
                                "memory": params['memory'],
                                "cpu": params['cpu'],
                                "tag": "XQuant RemoteSubmit Common Task",
                                "gpu": params['gpu'],
                                "preferred_gpu":preferred_gpu,
                                "image": image,
                                "group": group,
                                "taskParam": '',
                                "pycharm_group": pycharm_group,
                                "appid":appid
                                }

        app_id = 1
        port_url = ''
        password = ''
        running_timeout = 31104000000
        entry_file = entryFileName
        code_path = entryFilePath
        # ro_path_set = ''
        # rw_path_set = str([{'sourcePath':sourcePath,'targetPath':entryFilePath}])
        priority = 0

        del params["parallel_list"]
        if len(parallel_list)>100:
            print('pallerl_list is too long')
            sys.exit()
        for line in parallel_list:
            resource_config_["taskParam"] = line
            resource_config = json.dumps(resource_config_)
            params["parallel"] = line
            task_config = json.dumps(params)
            if len(task_config) > 900 or len(resource_config) > 900:
                print("aimr task's param is too long !")
                sys.exit(0)
            cursor.execute('SET character_set_connection=utf8;')
            ret = cursor.executemany(
                "insert into {}(user_id, xquant_id,fjob_id,resource_config,task_config,status,app_id,port_url,password,running_timeout,entry_file,code_path,ro_path_set,rw_path_set,log_keyprefix,priority)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                    tableName), [(user_id, xquant_id, fjob_id, resource_config, task_config, 0, app_id, port_url,
                                  password, running_timeout, entry_file, code_path, ro_path_set, rw_path_set,
                                  log_keyprefix, priority)])
            id_lis.append(cursor.lastrowid)
            db.commit()
        cursor.close()
        db.close()
        while True:
            db = pymysql.connect(databaseIp[0], "xquant_tyjk", "X7_mJw12m8UW", databaseName[0])
            cursor = db.cursor()
            cursor.execute(
                "select * from application where status in (0,1,3,6) and xquant_id=%s and fjob_id is not null" % xquant_id)
            data = cursor.fetchall()
            cursor.close()
            db.close()
            count = len(data)
            tmpcount = 0
            pycharm_count = 0
            is_pycharm = 0
            for i in range(count):
                taskinfo = data[i]
                status = taskinfo[7]
                task_group = json.loads(taskinfo[5])
                if 'pycharm_group' in task_group.keys():
                    is_pycharm = 1
                    if task_group['pycharm_group'] == pycharm_group:                        
                        pycharm_count += 1
                        if status in (0, 1, 3, 6):
                            time.sleep(3)
                            break
                        else:
                            tmpcount += 1
                elif status in (0, 1, 3, 6):
                    time.sleep(3)                    
                    break
                else:
                    tmpcount += 1
            if tmpcount == pycharm_count and is_pycharm == 1:
                break
            elif tmpcount == count and is_pycharm == 0:
                break 


def getParam():
    # f = open("/tmp/xquant_conf","r")
    filepath = os.getenv('XQUANT_CONF_FILE')
    f = open(filepath, "r")
    file = f.read()
    f.close()
    file = file.split('\n')
    param = file[5].split('=')[1]
    return param
# userid,xquant_id,task_config,fjob_id(),resource_config,

# param = {
#     "parallel_list": ["sfdsff","dddd","dsdgdgd"],
#     "docker_version": "htsc:latest",
#     "type": "gpu",
#     "is_sync":False,
#     "cpu":1,
#     "tag":"xquant",
#     "gpu":1,
#     "memory":12
# }
# run_tensorflow("a.py",json.dumps(param))