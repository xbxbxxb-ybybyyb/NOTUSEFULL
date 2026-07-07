import ray
from xfactor.Database import Database
import xfactor.FactorUtil as FactorUtil
from xquant.factordata import FactorData
import pandas as pd
import datetime as dt

fa = FactorData()


def __load_data(depend_data_type_list, stock_list, trading_day_list, input_factor_lib, *args):
    database = Database()
    data_info = {
        "depend_data": {},
        "depend_factors": {},
        "depend_nonfactors": {}
    }

    # 需要判断depend_data_type_list为空的情况（例如业务只用被依赖的因子做rolling等操作）
    if depend_data_type_list:
        data_type_list = list(filter(lambda x: "Basic_factor." in x and x[-7:]!="_minute", depend_data_type_list))
        minute_data_type_list = list(filter(lambda x: "Basic_factor." in x and x[-7:]=="_minute", depend_data_type_list))
        basic_str = "FactorData.Basic_factor."

        if data_type_list:
            basic_type_list = list(map(lambda x: x.split(".")[-1], data_type_list))
            data = fa.get_factor_value('Basic_factor', stock=stock_list, mddate=trading_day_list,
                                       factor_names=basic_type_list)
            for col in basic_type_list:
                database.update("depend_data", basic_str + col, data[col].unstack())
                data_info["depend_data"].update({basic_str + col: "DAY"})

        if minute_data_type_list:
            minute_path = "/data/user/666889/PanelMinData/stock/"
            basic_minute_type_list = list(map(lambda x: x.split(".")[-1], minute_data_type_list))

            begin_date = min(trading_day_list)
            last_date = max(trading_day_list)
            begin_month = begin_date[:6]
            last_month = last_date[:6]

            for col in basic_minute_type_list:
                data_info["depend_data"].update({basic_str + col: "MINUTE"})
                temp_col = col[:-7]
                temp_res_list = []
                for month in range(int(begin_month), int(last_month) + 1):
                    df = pd.read_pickle(minute_path + "{}/".format(temp_col) + str(month) + "_{}.pkl".format(temp_col))
                    temp_res_list.append(df)
                minute_data = pd.concat(temp_res_list, axis=0)
                minute_data = minute_data[(minute_data.index >= dt.datetime.strptime(begin_date, "%Y%m%d")) & (minute_data.index <= dt.datetime.strptime(last_date, "%Y%m%d") + dt.timedelta(hours=15))]
                database.update("depend_data", basic_str + col, minute_data)

        #TODO 财务数据

    if input_factor_lib == "nonfactor":
        for depend_nonfactor_name in args[0]:
            data_info["depend_nonfactors"].update({depend_nonfactor_name: "DAY"})
            data = fa.get_factor_value(input_factor_lib, stock=stock_list, mddate=trading_day_list,
                                       factor_names=[depend_nonfactor_name])[depend_nonfactor_name].unstack()
            database.update("depend_nonfactors", depend_nonfactor_name, data)

    elif input_factor_lib:
        for depend_factor_name in args[0]:
            data_info["depend_factors"].update({depend_factor_name: "DAY"})
            data = fa.get_factor_value(input_factor_lib, stock=stock_list, mddate=trading_day_list,
                                       factor_names=[depend_factor_name])[depend_factor_name].unstack()
            database.update("depend_factors", depend_factor_name, data)

    return database, data_info


# 获取指定batch依赖的数据集
def get_database_for_task(task):
    calc_datetime_list = task["calc_time_list"]
    factor_instance_list = task["factor_instance_list"]
    stock_list = task["stock_list"]
    full_datetime_list = task["full_datetime_list"]
    input_factor_lib = task["input_factor_lib"]

    max_data_exceed = FactorUtil.get_max_data_exceed(factor_instance_list)
    start_date = calc_datetime_list[0]
    end_date = calc_datetime_list[-1]
    require_date_list = full_datetime_list[
                        full_datetime_list.index(start_date) - max_data_exceed: full_datetime_list.index(end_date) + 1]

    depend_data_type_list = FactorUtil.get_factor_depend_data_types(factor_instance_list)

    # 通过判断input_factor_lib确定是否需要获取其他depend_factor
    # TODO 确认nonfactor的因子库名称
    if input_factor_lib == None:
        database, data_info = __load_data(depend_data_type_list, stock_list, require_date_list, input_factor_lib)
    elif input_factor_lib == "nonfactor":
        depend_nonfactor_list = FactorUtil.get_factor_depend_nonfactors(factor_instance_list)
        database, data_info = __load_data(depend_data_type_list, stock_list, require_date_list, input_factor_lib,
                                          depend_nonfactor_list)
    else:
        depend_factor_list = FactorUtil.get_factor_depend_factors(factor_instance_list)
        database, data_info = __load_data(depend_data_type_list, stock_list, require_date_list, input_factor_lib,
                                          depend_factor_list)

    return database, data_info


def save_factor(result, output_factor_lib):
    for factor_name, factor_value in result.items():
        try:
            fa.add_factor(output_factor_lib, [factor_name])
        except:
            pass
        factor_value.index.name = "mddate"
        factor_value.columns.name = "stock"
        factor_value = factor_value.unstack().to_frame()
        factor_value.columns = [factor_name]
        fa.update_factor_value(output_factor_lib, factor_value)
