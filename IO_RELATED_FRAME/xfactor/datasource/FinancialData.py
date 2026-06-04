import os
import pandas as pd
import datetime as dt
import settings
from h5data.IO import IO

H5_STR = "h5_"
WIND_STR = "WIND_"
GOGOAL_STR = "SUNTIME_"
CHARACTERISTIC_STR = "CHARACTERISTIC_"
# 基于h5的日频数据，需要按照日频数据的播放逻辑来播放，不能以普通的财务表来播放
SPECIAL_FINANCIAL_DATA_TYPE_LIST = ["FactorData.RISK_CHINA_STOCK_DAILY_STYLEFACTOR"]
READALL_FINANCIAL_TABLE_LIST = ["WIND_AShareProfitNotice"]


# 获取财务数据（即H5文件中的数据）
def get_data(table_name, start_date, end_date, col=None):
    if table_name in settings.H5_FILES_NO_FILTER.keys():
        table_path_list = table_name.split("_")
        path_list = [settings.H5_DATA_PATH, table_path_list[0], "_".join(table_path_list[1:3])]
        path_list.extend(table_path_list[3:])
        path_list.append("{}.h5".format(table_name))
        data = pd.read_hdf(os.path.join(*path_list))
        idx_names = settings.H5_FILES_NO_FILTER[table_name]
        data.index.rename(idx_names[0] if len(idx_names) == 1 else idx_names, inplace=True)
    else:
        # 原始财务数据表，在DATABASE目录下
        if table_name in settings.H5_FILES_FILTER_UNTIL_TODAY or WIND_STR in table_name or GOGOAL_STR in table_name or CHARACTERISTIC_STR in table_name:
            if table_name in settings.H5_FILES_FILTER_UNTIL_TODAY or table_name in READALL_FINANCIAL_TABLE_LIST:
                end_date = dt.datetime.today().strftime("%Y%m%d")
            if WIND_STR in table_name:
                source, sub_table_name = WIND_STR[:-1], table_name[5:]
            elif GOGOAL_STR in table_name:
                source, sub_table_name = GOGOAL_STR[:-1], table_name[8:]
            elif CHARACTERISTIC_STR in table_name:
                source, sub_table_name = CHARACTERISTIC_STR[:-1], table_name[15:]
            h5_path = os.path.join(settings.H5_DATA_PATH, "DATABASE", source, sub_table_name,
                                   "{}.h5".format(sub_table_name))
        else:
            # 加工后的财务数据表，和DATABASE目录平级，以后会调整目录结构
            table_path_list = table_name.split("_")
            path_list = [settings.H5_DATA_PATH, table_path_list[0], "_".join(table_path_list[1:3])]
            path_list.extend(table_path_list[3:])
            path_list.append("{}.h5".format(table_name))
            h5_path = os.path.join(*path_list)
        # h5多列提取，形式为"[colA，colB]"
        if col:
            if col[0].startswith("["):
                col = col[0][1: -1].split(",")
                col = list(map(lambda x: x.strip(), col))
            if table_name in settings.H5_FILE_FILTER_MAPPING:
                # 如果子类的depend_data没有筛选字段，新增筛选字段然后rename
                if settings.H5_FILE_FILTER_MAPPING[table_name] not in col:
                    col.append(settings.H5_FILE_FILTER_MAPPING[table_name])
                    data = IO.read_data(alt=h5_path, trading_days=[start_date, end_date], columns=col)
                    data = data.rename({settings.H5_FILE_FILTER_MAPPING[table_name]: "htsc_date"}, axis=1)
                else:
                    # 如果子类的depend_data有筛选字段，新增htsc_date
                    data = IO.read_data(alt=h5_path, trading_days=[start_date, end_date], columns=col)
                    data["htsc_date"] = data[settings.H5_FILE_FILTER_MAPPING[table_name]]
                # 如果stm_issuingdate为筛选字段，需要修改时间格式
                if settings.H5_FILE_FILTER_MAPPING[table_name] == "stm_issuingdate":
                    data["htsc_date"] = list(map(lambda x: dt.datetime.strptime(x, "%Y-%m-%d"), data["htsc_date"]))
                if settings.H5_FILE_FILTER_MAPPING[table_name] == "ENTRYDATE":
                    data["htsc_date"] = data[["ENTRYDATE", "ENTRYTIME"]].apply(
                        lambda x: dt.datetime.strptime(x["ENTRYDATE"][:10], "%Y-%m-%d") if x[
                                                                                               "ENTRYTIME"] > "05:00:00" else dt.datetime.strptime(
                            x["ENTRYDATE"][:10], "%Y-%m-%d") - dt.timedelta(1), axis=1)
            else:
                data = IO.read_data(alt=h5_path, trading_days=[start_date, end_date], columns=col)
        else:
            data = IO.read_data(alt=h5_path, trading_days=[start_date, end_date], columns=None)
            if table_name in settings.H5_FILE_FILTER_MAPPING:
                data["htsc_date"] = data[settings.H5_FILE_FILTER_MAPPING[table_name]]
                if settings.H5_FILE_FILTER_MAPPING[table_name] == "stm_issuingdate":
                    data["htsc_date"] = list(map(lambda x: dt.datetime.strptime(x, "%Y-%m-%d"), data["htsc_date"]))
                if settings.H5_FILE_FILTER_MAPPING[table_name] == "ENTRYDATE":
                    data["htsc_date"] = data[["ENTRYDATE", "ENTRYTIME"]].apply(
                        lambda x: dt.datetime.strptime(x["ENTRYDATE"][:10], "%Y-%m-%d") if x[
                                                                                               "ENTRYTIME"] > "05:00:00" else dt.datetime.strptime(
                            x["ENTRYDATE"][:10], "%Y-%m-%d") - dt.timedelta(1), axis=1)
        data.index.rename(["date", "stock"], inplace=True)
    return data


def filter_data_type(depend_data_type_list):
    special_data_type_list = list(filter(lambda x: x in SPECIAL_FINANCIAL_DATA_TYPE_LIST, depend_data_type_list))

    # 剔除需要按日播放的列表
    depend_data_type_list = list(set(depend_data_type_list) - set(SPECIAL_FINANCIAL_DATA_TYPE_LIST))

    # 金工组IO中可能用到所有标准格式h5
    h5str_list = ['INDEXWEIGHT', 'INDUSTRY', 'ETC', 'RISK', 'FDD', 'FCD', 'CALENDAR', 'UNIV', 'VD']
    # 合成表
    h5_data_type_list = list(
        filter(lambda x: "_" in x and x.split(".")[1].split("_")[0] in h5str_list, depend_data_type_list))

    # 万得落地库表
    wind_data_type_list = list(filter(lambda x: WIND_STR in x, depend_data_type_list))
    # 朝阳永续表
    gogoal_data_type_list = list(filter(lambda x: GOGOAL_STR in x, depend_data_type_list))
    # 特色数据表
    characteristic_data_type_list = list(filter(lambda x: CHARACTERISTIC_STR in x, depend_data_type_list))

    if len(h5_data_type_list + wind_data_type_list + gogoal_data_type_list) > 0:
        h5_data_type_list.extend(special_data_type_list)
        special_data_type_list = []

    financial_data_type_list = {
        H5_STR: h5_data_type_list,
        WIND_STR: wind_data_type_list,
        GOGOAL_STR: gogoal_data_type_list,
        CHARACTERISTIC_STR: characteristic_data_type_list,
        "SPECIAL": special_data_type_list
    }
    return financial_data_type_list
