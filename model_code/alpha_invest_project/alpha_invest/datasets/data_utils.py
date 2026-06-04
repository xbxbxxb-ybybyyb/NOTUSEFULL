from xquant.factordata import FactorData
import  datetime as dt
import numpy as np
import pandas as pd

def convert_date_or_time_int_to_datetime(date_time_input):
    # 将int型的日期或日期时间，转化为datetime型的；如输入单一值、则返回单一值；如输入list，则返回list
    # 可支持输入8位数的日期、例如20180509，也可支持输入14位数的日期时间、例如20180509145559
    # 但若输入的是list, 则list中元素的格式必须一样，不能8位和14位混淆
    if isinstance(date_time_input, list):
        original_input_is_list = True
    else:
        original_input_is_list = False
        date_time_input = [date_time_input]
    if (isinstance(date_time_input[0], int) or isinstance(date_time_input[0], np.int64)) \
            and str(date_time_input[0]).__len__() == 8:
        date_list_str = [str(i_date) for i_date in date_time_input]
        answer_list = [dt.datetime(int(i_date[0:4]), int(i_date[4:6]), int(i_date[6:8])) for i_date in date_list_str]
    elif (isinstance(date_time_input[0], int) or isinstance(date_time_input[0], np.int64)) \
            and str(date_time_input[0]).__len__() == 12:
        date_time_list_str = [str(i_date_time) for i_date_time in date_time_input]
        answer_list = [
            dt.datetime(int(i_date_time[0:4]), int(i_date_time[4:6]), int(i_date_time[6:8]), int(i_date_time[8:10]),
                        int(i_date_time[10:12])) for i_date_time in date_time_list_str]
    elif (isinstance(date_time_input[0], int) or isinstance(date_time_input[0], np.int64)) \
            and str(date_time_input[0]).__len__() == 14:
        date_time_list_str = [str(i_date_time) for i_date_time in date_time_input]
        answer_list = [
            dt.datetime(int(i_date_time[0:4]), int(i_date_time[4:6]), int(i_date_time[6:8]), int(i_date_time[8:10]),
                        int(i_date_time[10:12]), int(i_date_time[12:14])) for i_date_time in date_time_list_str]
    else:
        print("function convert_date_or_time_int_to_datetime: input type or format error")
        answer_list = []
    if not original_input_is_list:
        answer_list = answer_list[0]
    return answer_list

def convert_df_index_type(df_input, index_type_input, index_type_output) -> pd.DataFrame:
    """
    转化dataframe的索引的数据类型, timestamp是数字型的timestamp, timestamp2是类似datetime型的
    """
    df = df_input.copy()
    index_name = df.index.name
    if index_type_input == 'date_int' and index_type_output == 'timestamp':
        index_list = list(df.index)
        index_list_datetime = convert_date_or_time_int_to_datetime(index_list)
        index_list_timestamp = [i.timestamp() for i in index_list_datetime]
        df['timestamp'] = index_list_timestamp
        df = df.set_index(['timestamp'])
    elif index_type_input == 'date_int' and index_type_output == 'datetime':
        index_list = list(df.index)
        index_list_datetime = convert_date_or_time_int_to_datetime(index_list)
        df['datetime'] = index_list_datetime
        df = df.set_index(['datetime'])
    elif index_type_input == 'date_time_int_multi_index' and index_type_output == 'timestamp':
        index_list = list(df.index)
        index_list = [x[0] * 1000000 + x[1]*100 for x in index_list]
        index_list_datetime = convert_date_or_time_int_to_datetime(index_list)
        index_list_timestamp = [i.timestamp() for i in index_list_datetime]
        df['timestamp'] = index_list_timestamp
        df = df.set_index(['timestamp'])
    elif index_type_input == 'timestamp' and index_type_output == 'date_time_int_multi_index':
        index_list = list(df.index)
        index_date_time_list = [dt.datetime.fromtimestamp(i) for i in index_list]
        date_int_list = [int((i.year * 10000 + i.month * 100 + i.day)) for i in index_date_time_list]
        time_int_list = [int((i.hour * 100 + i.minute)) for i in index_date_time_list]
        df['date'] = date_int_list
        df['time'] = time_int_list
        df = df.set_index(['date', 'time'])
    elif index_type_input == 'timestamp' and index_type_output == 'date_int':
        index_list = list(df.index)
        index_date_time_list = [dt.datetime.fromtimestamp(i) for i in index_list]
        date_int_list = [int((i.year * 10000 + i.month * 100 + i.day)) for i in index_date_time_list]
        df['date'] = date_int_list
        df = df.set_index(['date'])
    elif index_type_input == 'timestamp' and index_type_output == 'date14_int':
        index_list = list(df.index)
        index_date_time_list = [dt.datetime.fromtimestamp(i) for i in index_list]
        date_int_list = [int(
            (i.year * 10000000000 + i.month * 100000000 + i.day * 1000000 + i.hour * 10000 + i.minute * 100 + i.second))
                         for i in index_date_time_list]
        df['date'] = date_int_list
        df = df.set_index(['date'])
    elif index_type_input in ['timestamp2', 'datetime'] and index_type_output == 'date_int':
        index_list = list(df.index)
        date_int_list = [int((i.year * 10000 + i.month * 100 + i.day)) for i in index_list]
        df['date'] = date_int_list
        df = df.set_index(['date'])
    elif index_type_input == 'str' and index_type_output == 'date_int':
        df = df.reset_index()
        df['date'] = df[index_name].astype(int)
        df = df.set_index(['date'])
    elif index_type_input == 'timestamp' and index_type_output == 'datetime':
        index_list = list(df.index)
        output_index = pd.to_datetime(list(map(pd.datetime.fromtimestamp, index_list)))
        df.index = output_index
    if index_name in list(df.columns):  # 原有的index列可能残留，删除之
        df = df.drop(index_name, axis=1)
    return df

def get_n_days_off(key_date, n_days_off):
    fa = FactorData()
    days = []
    if n_days_off == 0:
        pass
    elif n_days_off<0:
        days = fa.tradingday(key_date, n_days_off)
    else:
        days = fa.tradingday(key_date, n_days_off)
    return days

if __name__=="__main__":
    print(get_n_days_off("20190701", 5))
    print(get_n_days_off("20190701", -5))
