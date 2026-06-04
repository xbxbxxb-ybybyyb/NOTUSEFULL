import os
import pandas as pd
import datetime as dt
from xfactor.Database import Database
from xfactor.FactorLib import FactorLib
import xfactor.FactorUtil as FactorUtil
import xfactor.Util as Util
from xfactor.datasource import DailyData, FinancialData, FactorData, MinuteData

import settings


# 更新h5表的database和datainfo
def __update_single_financial_data(database, data_info, financial_data_type, col, data, type_info):
    if col:
        financial_data_type = financial_data_type + "." + col[0]
    database.update("depend_data", financial_data_type, data)
    data_info["depend_data"].update({financial_data_type: type_info})


# 更新分钟数据的database和datainfo
def __update_minute_data(database, data_info, basic_minute_type_list, begin_date, last_date, basic_str, stock_list):
    # 根据股票组获取分钟线数据时需要指定月份
    for col in basic_minute_type_list:
        minute_data = MinuteData.get_history_data(col, begin_date, last_date, stock_list)
        database.update("depend_data", basic_str + col, minute_data)
        data_info["depend_data"].update({basic_str + col: "MINUTE"})


# 分别从两个路径获取分钟数据
# 包括历史分钟数据（截至昨天的） 和  今天的分钟数据（截至触发点当前的）
def __update_minute_data_for_realtime(database, data_info, basic_minute_type_list, begin_date, last_date,
                                      basic_str,
                                      stock_list, realtime_minute_path, cache=None):
    # 根据股票组获取分钟线数据时需要指定月份
    date_list = Util.get_trading_day(begin_date, last_date)
    for col in basic_minute_type_list:
        if len(date_list) > 1:
            minute_data = MinuteData.get_history_data(col, date_list[0], date_list[-2], stock_list, cache)
            realtime_minute_data = MinuteData.get_realtime_data(col, realtime_minute_path, stock_list)
            minute_data = minute_data.append(realtime_minute_data)
        else:
            # 因子中的minute_lag 为 0
            minute_data = MinuteData.get_realtime_data(col, realtime_minute_path, stock_list)
        database.update("depend_data", basic_str + col, minute_data)
        data_info["depend_data"].update({basic_str + col: "MINUTE"})


# 获取数据
def __load_data(depend_data_type_list, stock_list, start_date, end_date, minute_start_date, financial_start_date,
                input_factor_lib, run_type, realtime_minute_data_path=None, cache=None, *args):
    database = Database()
    data_info = {
        "depend_data": {},
        "depend_factors": {},
        "depend_nonfactors": {}
    }

    # 需要判断depend_data_type_list为空的情况（例如业务只用被依赖的因子做rolling等操作）
    if depend_data_type_list:
        # 过滤出财务数据
        financial_data_type_list = FinancialData.filter_data_type(depend_data_type_list)

        # 过滤出分钟数据
        minute_data_type_list = MinuteData.filter_data_type(depend_data_type_list)

        # 过滤出日频数据
        daily_type_list = DailyData.filter_data_type(depend_data_type_list)

        basic_str = "FactorData.Basic_factor."

        # 分钟频基础数据
        if minute_data_type_list:
            basic_minute_type_list = list(map(lambda x: x.split(".")[2], minute_data_type_list))
            begin_date = minute_start_date
            last_date = end_date
            if run_type == "offline":
                __update_minute_data(database, data_info, basic_minute_type_list, begin_date, last_date, basic_str,
                                     stock_list)
            else:
                __update_minute_data_for_realtime(database, data_info, basic_minute_type_list, begin_date, last_date,
                                                  basic_str,
                                                  stock_list, realtime_minute_data_path, cache)

        # 财务数据,包括万得、朝阳永续、合成表
        if financial_data_type_list:
            pre_str = "FactorData."
            for data_source, data_type_list in financial_data_type_list.items():
                this_start_date = financial_start_date
                if data_source == "SPECIAL":
                    data_info_type = "DAY"
                    this_start_date = start_date
                else:
                    data_info_type = "{}FINANCIAL".format(data_source)
                for data_type in data_type_list:
                    table_name = data_type.split(".")[1]
                    col = [data_type.split(".")[2]] if data_type.count(".") == 2 else None
                    data = FinancialData.get_data(table_name, this_start_date, end_date, col)
                    __update_single_financial_data(database, data_info, pre_str + table_name, col, data,
                                                   data_info_type)

        # 日频基础数据
        if daily_type_list:
            # 示例，包括股票和指数["close", "volume-000001.SH", ]
            basic_type_list = list(map(lambda x: x.split(".", 2)[2], daily_type_list))
            index_basic_type_list = list(filter(lambda x: "-" in x, basic_type_list))
            stock_basic_type_list = list(filter(lambda x: "-" not in x, basic_type_list))

            # 修正股票日频数据，分离依赖的h5数据
            daily_h5_list = ["Data_twap", "Data_suspension", "Data_limit_pctg"]
            daily_h5_list = list(filter(lambda x: x in daily_h5_list, stock_basic_type_list))
            stock_basic_type_list = list(
                filter(lambda x: x not in daily_h5_list, stock_basic_type_list))

            # 股票日频数据，不包括少量h5数据
            if stock_basic_type_list:
                for col in stock_basic_type_list:
                    df = DailyData.get_data(data_type="stock", stock_list=stock_list, start_date=start_date,
                                            end_date=end_date,
                                            factor_name=col)
                    database.update("depend_data", basic_str + col, df)
                    data_info["depend_data"].update({basic_str + col: "DAY"})
            # 少量h5日频数据
            if daily_h5_list:
                for item in daily_h5_list:
                    df = pd.read_hdf(os.path.join(settings.DAILY_DATA_PATH, "{}.h5".format(item)), '/factor')
                    df.index = list(map(lambda x: str(x), df.index))
                    # df = df.reindex(columns=stock_list)
                    database.update("depend_data", basic_str + item, df)
                    data_info["depend_data"].update({basic_str + item: "DAY"})
            # 指数日频数据
            if index_basic_type_list:
                for item in index_basic_type_list:
                    df = DailyData.get_data(data_type="index", stock_list=[item.split("-")[1]],
                                            start_date=start_date, end_date=end_date,
                                            factor_name=item.split("-")[0])
                    database.update("depend_data", basic_str + item, df)
                    data_info["depend_data"].update({basic_str + item: "DAY"})

    if input_factor_lib:
        for depend_name in args[0]:
            data_info[args[1]].update({depend_name: "DAY"})
            data = FactorData.get_data(input_factor_lib, stock_list, start_date, end_date, depend_name)
            database.update(args[1], depend_name, data)
    return database, data_info


#    获取指定batch依赖的数据集
#    run_type: online/offline
def get_database_for_task(task, run_type, realtime_minute_data_path=None, cache=None):
    calc_datetime_list = task["calc_time_list"]
    factor_class_list = task["factor_class_list"]
    full_datetime_list = task["full_datetime_list"]
    input_factor_lib = task["input_factor_lib"]

    max_daily_data_exceed = FactorUtil.get_max_daily_data_exceed(factor_class_list)
    max_minute_data_exceed = FactorUtil.get_max_minute_data_exceed(factor_class_list)
    max_financial_data_exceed = FactorUtil.get_max_financial_data_exceed(factor_class_list)

    start_date, end_date = calc_datetime_list[0], calc_datetime_list[-1]
    start_date_index, end_date_index = full_datetime_list.index(start_date), full_datetime_list.index(end_date)

    require_date_list = full_datetime_list[start_date_index - max_daily_data_exceed: end_date_index + 1]
    minute_start_date = full_datetime_list[start_date_index - max_minute_data_exceed]
    financial_start_date = dt.datetime.strptime(full_datetime_list[start_date_index - max_financial_data_exceed],
                                                "%Y%m%d")
    depend_data_type_list = FactorUtil.get_factor_depend_data_types(factor_class_list)
    depend_nonfactor_list = FactorUtil.get_factor_depend_nonfactors(factor_class_list)
    depend_factor_list = FactorUtil.get_factor_depend_factors(factor_class_list)
    stock_list = Util.get_stock_list()
    # 通过判断input_factor_lib确定是否需要获取其他depend_factor
    if input_factor_lib is None:
        database, data_info = __load_data(depend_data_type_list, stock_list, require_date_list[0],
                                          require_date_list[-1], minute_start_date,
                                          financial_start_date, input_factor_lib, run_type, realtime_minute_data_path,
                                          cache)
    elif depend_nonfactor_list:
        database, data_info = __load_data(depend_data_type_list, stock_list, require_date_list[0],
                                          require_date_list[-1], minute_start_date,
                                          financial_start_date, input_factor_lib, run_type, realtime_minute_data_path,
                                          cache,
                                          depend_nonfactor_list,
                                          "depend_nonfactors")
    else:
        database, data_info = __load_data(depend_data_type_list, stock_list, require_date_list[0],
                                          require_date_list[-1], minute_start_date,
                                          financial_start_date, input_factor_lib, run_type, realtime_minute_data_path,
                                          cache,
                                          depend_factor_list,
                                          "depend_factors")
    return database, data_info


def save_factor(factor_result, output_factor_lib):
    factor_lib = FactorLib(output_factor_lib)
    for factor_name, factor_value in factor_result.items():
        factor_lib.update_factor_value(factor_name, factor_value)
