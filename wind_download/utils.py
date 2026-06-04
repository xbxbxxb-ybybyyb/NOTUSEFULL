# -*- coding: utf-8 -*-
"""
Created on Tue May 22 17:00:00 2018

@author: 012315  015623
"""
import os
import settings
from loguru import logger
import subprocess


def create_flag(file_name, edate):
    flag_root = os.path.join(settings.LOCAL_FLAG_DIR, str(edate))
    if not os.path.exists(flag_root):
        os.makedirs(flag_root)
    flag_file = os.path.join(flag_root, file_name)
    with open(flag_file, 'w'):
        pass


def repack_file(file):
    if not os.path.exists(file):
        logger.warning("repack文件不存在：file={}".format(file))
        return
    out_file = os.path.join(os.path.dirname(file), "out.h5")
    logger.info("开始repack： file={}".format(file))
    subprocess.call(["ptrepack", file, out_file])
    raw_size = round(os.path.getsize(file) / 1024 / 1024 / 1024, 2)
    new_size = round(os.path.getsize(out_file) / 1024 / 1024 / 1024, 2)
    logger.info("结束repack： file={}, raw_size={}GB, new_size={}GB".format(file, raw_size, new_size))
    subprocess.call(["mv", out_file, file])
    logger.info("结束mv： file={}".format(file))
