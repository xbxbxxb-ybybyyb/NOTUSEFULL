import os
import time
import pickle
import traceback
from DataInterface.Config import USER_ID, CELL_SIZE
from DataInterface.Config import TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from DataInterface.Config import TICK_STOCK_HBASE_COLUMNS, TICK_CBOND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from DataInterface.Config import TRANSACTION_STOCK_HBASE_COLUMNS, TRANSACTION_CBOND_HBASE_COLUMNS, TRANSACTION_FUND_HBASE_COLUMNS
from DataInterface.Config import ORDER_STOCK_HBASE_COLUMNS, ORDER_CBOND_HBASE_COLUMNS, ORDER_FUND_HBASE_COLUMNS
from Utils.HelpFunc import get_code_type, my_print
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile


def fix_df_columns(code_type, data_type, tick_df):
    """ Spark更新数据存到HDFS中时可能出现列名乱码情况，重新设置正确列名
    """
    rename = False

    if data_type == TICK_SUFFIX:
        if code_type == "STOCK":
            HBASE_COLUMNS = TICK_STOCK_HBASE_COLUMNS
        elif code_type == "CBOND":
            HBASE_COLUMNS = TICK_CBOND_HBASE_COLUMNS
        elif code_type == "ETF" or code_type == "LOF":
            HBASE_COLUMNS = TICK_FUND_HBASE_COLUMNS
        elif code_type == "INDEX" or code_type == "INDUSTRY":
            HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
        elif code_type == "FUTURE":
            HBASE_COLUMNS = TICK_FUTURE_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Tick Rename Columns : {} ".format(code_type))

    elif data_type == TRANSACTION_SUFFIX:
        if code_type == "STOCK":
            HBASE_COLUMNS = TRANSACTION_STOCK_HBASE_COLUMNS
        elif code_type == "CBOND":
            HBASE_COLUMNS = TRANSACTION_CBOND_HBASE_COLUMNS
        elif code_type == "ETF" or code_type == "LOF":
            HBASE_COLUMNS = TRANSACTION_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Transaction Rename Columns : {} ".format(code_type))

    elif data_type == ORDER_SUFFIX:
        if code_type == "STOCK":
            HBASE_COLUMNS = ORDER_STOCK_HBASE_COLUMNS
        elif code_type == "CBOND":
            HBASE_COLUMNS = ORDER_CBOND_HBASE_COLUMNS
        elif code_type == "ETF" or code_type == "LOF":
            HBASE_COLUMNS = ORDER_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Order Rename Columns : {} ".format(code_type))

    else:
        raise Exception(" Not Support Rename Data Type: {} ".format(data_type))

    for col in tick_df.columns:
        if col not in HBASE_COLUMNS:
            rename = True
            break

    if rename:
        tick_df.columns = HBASE_COLUMNS

    return tick_df


class DumpFileHbase:
    def __init__(self, library, hdfs_path, data_type, code, date_list):
        self.library = library
        self.hdfs_path = hdfs_path
        self.data_type = data_type
        self.code = code
        self.code_type = get_code_type(self.code)
        self.date_list = date_list

        self.fa = FactorData()
        self.hf = HDFSFile()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def run(self):
        t1 = time.time()

        my_print(" Start Dump {} Data: {}-{} Dates ".format(self.data_type, self.code, len(self.date_list)))

        root = USER_ID if self.is_executor else ""
        path = os.path.join(root, self.hdfs_path + "/{}/".format(self.data_type))

        for update_date in self.date_list:
            file_name = os.path.join(path, "{}_{}_{}.pickle".format(self.code, update_date, update_date))
            if self.hf.exists(file_name):
                with self.hf.open(file_name, "rb") as f:
                    data = f.read()
                    df = pickle.loads(data)

                df = fix_df_columns(self.code_type, self.data_type, df)

                try:
                    if not df.empty:
                        self.fa.update_factor_value(self.library, df, self.code, update_date, cell_size=CELL_SIZE)
                    self.hf.delete(file_name)
                except:
                    traceback.print_exc()
                    my_print(" Dump File with CELL_SIZE ERROR: {} ".format(file_name))
            else:
                my_print(" File Not Exists: {} ".format(file_name))

        my_print(" {} Dump {} Data Cost: {} ".format(self.code, self.data_type, round(time.time() - t1, 2)))


class TaskMeta(object):
    def __init__(self, library, hdfsPath, dataType, code, dateList):
        self.__library = library
        self.__hdfsPath = hdfsPath
        self.__dataType = dataType
        self.__code = code
        self.__dateList = dateList

    def getLibrary(self):
        return self.__library

    def getHdfsPath(self):
        return self.__hdfsPath

    def getDataType(self):
        return self.__dataType

    def getCode(self):
        return self.__code

    def getDateList(self):
        return self.__dateList

def get_code_date_dict(root_path, data_type):
    """"""
    if data_type == "Tick":
        prefix = TICK_SUFFIX
    elif data_type == "Transaction":
        prefix = TRANSACTION_SUFFIX
    elif data_type == "Order":
        prefix = ORDER_SUFFIX

    hdfs_path = root_path + "/{}/".format(prefix)

    hf = HDFSFile()

    codeDateDict = dict()

    if not hf.exists(hdfs_path):
        return codeDateDict

    all_files = hf.listdir(hdfs_path)
    code_list = sorted(list(set([file.split("_")[0] for file in all_files])))

    for code in code_list:
        date_list = sorted(list(set([file.split("_")[1] for file in all_files if file.split("_")[0] == code])))
        if len(date_list) > 0:
            codeDateDict[code] = date_list

    return codeDateDict




