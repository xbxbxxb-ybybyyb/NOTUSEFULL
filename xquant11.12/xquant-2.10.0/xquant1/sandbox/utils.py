import os
import argparse

import json

_noParmission = "Permission Denied"
_open_mode_limit = ["w", "a", "x"]  # 判断的文件模式
_opDir = []

def _check_Dir_Permissions(path):
    if isinstance(path, int):
        return True

    if path.find('.ipython') > -1:
        return True
    
    if path == '/dev/null':
        return True

    global _opDir
    (fp,fn) = os.path.split(path)
    fullpath = os.path.abspath(fp) + '/'  # 放入完整文件路径
    for opDir in _opDir:
        if fullpath.find(opDir) == 0 :
            return True
    return False

def _init_args():
    from xquant1.pyfile import setPyfilePath
    global _opDir
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", help="get user name")
    parser.add_argument("-j", "--jobid", help="get job id")
    parser.add_argument("-t", "--run-type", help="get run type")
    parser.add_argument("-f", "--filename", help="get filename")
    t = parser.parse_args()
    if not t.user:
        raise Exception("xquant system lack  user name")

    shareDirList = setPyfilePath.__xquant_config_dict.get('shareDirList')
    orgIdList = []
    for shareDir in shareDirList:
        if shareDir.get("isAdmin"):
            orgId = shareDir['orgId']
            orgIdList.append(orgId)
    _opDir = [os.getcwd() + "/", "/tmp/", "/dev/shm/","/app/data/" + t.user + "/","/data/"]
    os.environ['USER_ID'] = t.user
    for orgId in orgIdList:
        _opDir.append("/app/data/SHARE_" + str(orgId) + "/")
        _opDir.append("/data/SHARE_" + str(orgId) + "/")

    #print("opdir----->",_opDir)