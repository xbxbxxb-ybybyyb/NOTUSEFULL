#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/5 14:32
import os

USER_ID = "013050"

def get_hdfs_root_path(mode, path):
    if mode == "Local":
        return os.path.join("", path)
    elif mode == "Spark":
        return os.path.join(USER_ID, path)
    else:
        raise Exception("ONLY SUPPORT LOCAL OR SPARK MODE")


