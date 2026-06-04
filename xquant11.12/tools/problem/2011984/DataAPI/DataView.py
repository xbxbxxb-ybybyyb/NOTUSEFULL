"""json与pickle文件读写"""

import os
import pickle
import json
import pandas as pd
from xquant.xqutils.xqfile import HDFSFile


def make_dir(file_dir, dfs=None):
    if file_dir.startswith('/data/user/'):  # NFS
        os.makedirs(file_dir, exist_ok=True)
    else:  # HDFS
        py = HDFSFile(dfs)
        py.mkdir(file_dir)


def file_exist(file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        return os.path.exists(file_name)
    else:  # HDFS
        py = HDFSFile(dfs)
        return py.exists(file_name)


def file_list_dir(file_dir, dfs=None):
    if file_dir.startswith('/data/user/'):  # NFS
        return os.listdir(file_dir)
    else:  # HDFS
        py = HDFSFile(dfs)
        return py.listdir(file_dir)


def load_pickle_file(file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'rb') as f:
            data = pickle.load(f)
    else:  # HDFS
        py = HDFSFile(dfs)
        with py.open(file_name, 'rb') as f:
            data = f.read()
            data = pickle.loads(data)
    return data


def save_pickle_file(data, file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'wb') as f:
            pickle.dump(data, f)
    else:
        py = HDFSFile(dfs)
        with py.open(file_name, 'wb') as f:  # HDFS
            pickle.dump(data, f)


def load_json_file(file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'r') as f:
            data = json.load(f)
    else:
        py = HDFSFile(dfs)
        with py.open(file_name, 'rb') as f:  # HDFS
            data = json.load(f)
    return data


def save_json_file(data, file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'w') as f:
            json.dump(data, f)
    else:
        py = HDFSFile(dfs)
        with py.open(file_name, 'wb') as f:  # HDFS
            json.dump(data, f)


def load_excel_file(file_name, sheet_name=0, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'rb') as f:
            data = pd.read_excel(f, sheet_name=sheet_name)
    else:
        py = HDFSFile(dfs)
        with py.open(file_name, 'rb') as f:  # HDFS
            data = pd.read_excel(f, sheet_name=sheet_name)
    return data
