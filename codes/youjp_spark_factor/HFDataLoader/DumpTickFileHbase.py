import os
import sys
import time
import pickle
import traceback
from HFDataLoader.Config import TICK_SUFFIX, TICK_STOCK_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from HFDataLoader.Config import TICK_CBOND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS
from HFDataLoader.Config import USER_ID, CELL_SIZE
import Utils.HelpFunc as Util
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from xquant.compute.sparkmr import remote_print

def fix_tick_df_columns(code_type, tick_df):
    """ Spark更新TICK数据存到HDFS中时可能出现列名乱码情况，重新设置正确列名
    """
    rename = False
    if code_type == "STOCK":
        HBASE_COLUMNS = TICK_STOCK_HBASE_COLUMNS
    elif code_type == "INDEX" or code_type == "INDUSTRY":
        HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
    elif code_type == "CBOND":
        HBASE_COLUMNS = TICK_CBOND_HBASE_COLUMNS
    elif code_type == "ETF" or code_type == "LOF":
        HBASE_COLUMNS = TICK_FUND_HBASE_COLUMNS
    elif code_type == "FUTURE":
        HBASE_COLUMNS = TICK_FUTURE_HBASE_COLUMNS
    else:
        raise Exception("Not Supported Code Type Yet: {}".format(code_type))

    for col in tick_df.columns:
        if col not in HBASE_COLUMNS:
            rename = True
            break
    if rename:
        tick_df.columns = HBASE_COLUMNS
    return tick_df


class DumpTickFileHbase:
    def __init__(self, lib_name, hdfs_path, code, date_list, hbase=False, env="Docker"):
        self.lib_name = lib_name
        self.hdfs_path = hdfs_path
        self.code = code
        self.code_type = Util.get_code_type(self.code)
        self.date_list = date_list
        self.hbase = hbase
        self.env = env
        self.fa = FactorData()
        self.hf = HDFSFile()

    def run_dump(self):
        t1 = time.time()
        self.my_print("Start Dump Tick Data: {}-{} Dates".format(self.code, len(self.date_list)))
        for update_date in self.date_list:
            if self.env=="Docker":
                path = self.hdfs_path
            elif self.env=="Spark":
                path = os.path.join(USER_ID, self.hdfs_path)
            file_name = os.path.join(path, "{}_{}_{}.pkl".format(self.code, update_date, update_date))
            if self.hf.exists(file_name):
                with self.hf.open(file_name, "rb") as f:
                    data = f.read()
                    tick_df = pickle.loads(data)
                tick_df = fix_tick_df_columns(self.code_type, tick_df)
                if self.hbase:
                    try:
                        self.fa.update_factor_value(self.lib_name, tick_df, "{0}_{1}".format(self.code, TICK_SUFFIX),
                                         update_date, cell_size=CELL_SIZE)
                        self.hf.delete(file_name)
                    except:
                        traceback.print_exc()
                        self.my_print("Dump File with CELL_SIZE ERROR: {}".format(file_name))
                else:
                    #space = sys.getsizeof(tick_df) / 1024 / 1024
                    # if space < 10:
                    try:
                        self.fa.update_factor_value(self.lib_name, tick_df, "{0}_{1}".format(self.code, TICK_SUFFIX), update_date)
                        self.hf.delete(file_name)
                    #else:
                    except:
                        traceback.print_exc()
                        if self.env=="Docker":
                            self.my_print("File Size Too Large, NAS File Saved")
                            nas_path = "/data/user/015629/HFDataDump/T"
                            if not os.path.exists(nas_path):
                                os.makedirs(nas_path)
                            pkl_file = os.path.join(nas_path, "{}_{}_{}.pkl".format(self.code, update_date, update_date))
                            with open(pkl_file, 'wb') as f:
                                pickle.dump(tick_df, f)
                            self.hf.delete(file_name)
                        else:
                            pass
            else:
                self.my_print("File Not Exists: {}".format(file_name))

        self.my_print("{} Dump Tick Data Cost: {} ".format(self.code, str(time.time() - t1)))

    def my_print(self, x_str):
        if self.env=="Docker":
            print(x_str)
        elif self.env=="Spark":
            remote_print(x_str)
        else:
            raise ValueError("Not Supported Env Yet")


class DumpTickFileHbase2:
    def __init__(self, lib_name, nas_path, code, date_list ):
        self.lib_name = lib_name
        self.nas_path = nas_path
        self.code = code
        self.code_type = Util.get_code_type(self.code)
        self.date_list = date_list

        self.fa = FactorData()

    def run_dump(self):
        t1 = time.time()
        print("Start Dump Tick Data: {}-{} Dates".format(self.code, len(self.date_list)))
        for update_date in self.date_list:
            file_name = os.path.join(self.nas_path, "{}_{}_{}.pkl".format(self.code, update_date, update_date))
            if os.path.exists(file_name):
                with open(file_name, "rb") as f:
                    data = f.read()
                    tick_df = pickle.loads(data)
                tick_df = fix_tick_df_columns(self.code_type, tick_df)
                try:
                    self.fa.update_factor_value(self.lib_name, tick_df, "{0}_{1}".format(self.code, TICK_SUFFIX),
                                                update_date, cell_size=CELL_SIZE)
                    os.remove(file_name)
                except:
                    traceback.print_exc()
                    print("Dump NAS Tick File To HBASE Fail: {}".format(file_name))
            else:
                print("File Not Exists: {}".format(file_name))

        print("{} Dump Tick Data Cost: {} ".format(self.code, str(time.time() - t1)))


def get_codeDateDict_HDFS(hdfs_path="HFDataDump/T/",
                           save=True,
                           save_path='/data/user/015629/MISC/codeDateDictHDFS.pkl'):
    """ 获取HDFS路径位置已有TICK数据股票-日期字典
    """
    hf = HDFSFile()
    codeDateDict = {}
    if not hf.exists(hdfs_path):
        return codeDateDict
    all_files = hf.listdir(hdfs_path)
    code_list = sorted(list(set([file.split("_")[0] for file in all_files])))

    for code in code_list:
        date_list = sorted(list(set([file.split("_")[1] for file in all_files if file.split("_")[0] == code])))
        if len(date_list) > 0:
            codeDateDict[code] = date_list

    if save:
        with open(save_path, 'wb') as f:
            pickle.dump(codeDateDict, f)

    return codeDateDict

def get_codeDateDict_NAS(nas_path="/data/user/015629/HFDataDump/T/",
                          save=True,
                          save_path='/data/user/015629/MISC/codeDateDictNAS.pkl'):
    """ 获取NAS路径位置已有TICK数据股票-日期字典
    """
    codeDateDict = {}
    if not os.path.exists(nas_path):
        return codeDateDict
    all_files = os.listdir(nas_path)
    code_list = sorted(list(set([file.split("_")[0] for file in all_files])))

    for code in code_list:
        date_list = sorted(list(set([file.split("_")[1] for file in all_files if file.split("_")[0] == code])))
        if len(date_list) > 0:
            codeDateDict[code] = date_list

    if save:
        with open(save_path, 'wb') as f:
            pickle.dump(codeDateDict, f)

    return codeDateDict




