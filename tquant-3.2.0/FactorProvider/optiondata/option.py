# _*_ coding:utf-8 _*_
import threading
import time
import pandas as pd
import datetime as dt
from FactorProvider.storage.db import DML_mysql
from FactorProvider.setEnv import xquantEnv, sysFlag
from FactorProvider.utils.utils import is_valid_date

# 实例化连接池与数据访问层类
if sysFlag == "xquant" or sysFlag == "big_data":
    dml = DML_mysql('xquant_wind')
else:
    raise Exception("未知运行系统异常！")


class OptionDataFP:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls)
            cls.__instance = obj
            return cls.__instance

    def __init__(self):
        self.today = dt.datetime.now()
        self.descriptionchange_df = None

    def __trans_params(self, params):
        if not params:
            return None
        if isinstance(params, str):
            param_res = "(" + "'" + params + "'" + ")"
        elif isinstance(params, list):
            params = list(set(params))
            if len(params) == 1:
                param_res = "(" + "'" + params[0] + "'" + ")"
            else:
                param_res = "(" + "'" + "','".join(params) + "'" + ")"
        else:
            raise Exception("params 为string类型，或list)类型! ")
        return param_res

    def __fetch_opt_des_change_by_contract_code(self, contract_code, c_name):
        """
        find the contract change info by the CONTRACT WIND CODE
        """
        if self.descriptionchange_df is None:
            sql = """
                    select S_CHANGE_DATE,S_INFO_NAME_OLD,S_EXERCISE_PRICE_OLD,S_INFO_CODE_OLD,S_UNIT_OLD,S_INFO_WINDCODE
                    from xquant_wind.coptiondescriptionchange
                  """.format(contract_code)
            self.descriptionchange_df = dml.getAllByPandas(c_name, sql)
        df_res = self.descriptionchange_df[self.descriptionchange_df["S_INFO_WINDCODE"] == contract_code]

        return df_res

    def __restore_option_status_to_day(self, c_name, ocs_data, date):
        for option in ocs_data.itertuples():
            option_chg_history = self.__fetch_opt_des_change_by_contract_code(option.Symbol, c_name)
            if (len(option_chg_history) == 0 or
                    len(option_chg_history[option_chg_history["S_CHANGE_DATE"] > date]) == 0):
                continue
            else:
                related_change = option_chg_history[option_chg_history["S_CHANGE_DATE"] > date].iloc[0]
                ocs_data.loc[option.Index, ["Name", "StrikePrice", "ModifiedSymbol", "ContractCount"]] = \
                    [related_change["S_INFO_NAME_OLD"], related_change["S_EXERCISE_PRICE_OLD"],
                     related_change["S_INFO_CODE_OLD"], related_change["S_UNIT_OLD"]]
                ocs_data.loc[option.Index, "AdjustSign"] = (
                    "M" if "M" in related_change["S_INFO_CODE_OLD"] else related_change["S_INFO_NAME_OLD"][-1])
        return ocs_data

    def __process_data(self, ocs_df, contpro_df_, date):
        ocs_df = ocs_df[(ocs_df["S_INFO_FTDATE"] <= date) & (ocs_df["S_INFO_LASTTRADINGDATE"] >= date)]
        ocs_df = ocs_df[["S_INFO_EXCODE", "S_INFO_EXNAME", "S_INFO_WINDCODE", "S_INFO_MONTH", "S_INFO_STRIKEPRICE",
                         "S_INFO_FTDATE", "S_INFO_LASTTRADINGDATE", "S_INFO_EXERCISINGEND",
                         "S_INFO_LDDATE", "ADJ_SIGN", "S_INFO_COUNIT", "S_INFO_SCCODE", "S_INFO_CALLPUT"]]
        ocs_df = ocs_df.rename({
            "S_INFO_EXCODE": "ModifiedSymbol",
            "S_INFO_EXNAME": "Name",
            "S_INFO_WINDCODE": "Symbol",
            "S_INFO_MONTH": "ExpireMonth",
            "S_INFO_STRIKEPRICE": "StrikePrice",
            "S_INFO_FTDATE": "StartTradingDate",
            "S_INFO_LASTTRADINGDATE": "LastTradingDate",
            "S_INFO_EXERCISINGEND": "ExercisingDate",
            "S_INFO_LDDATE": "DeliveryDate",
            "ADJ_SIGN": "AdjustSign",
            "S_INFO_COUNIT": "ContractCount",
            "S_INFO_CALLPUT": "CallOrPut"
        }, axis=1).reset_index(drop=True)
        ocs_df = pd.merge(ocs_df, contpro_df_, how="left", left_on="S_INFO_SCCODE", right_on="S_INFO_CODE")
        # 把冗余列删除
        ocs_df.drop(["S_INFO_CODE", "S_INFO_SCCODE", "S_INFO_NAME", "filter"], axis=1, inplace=True)
        ocs_df["ExpireMonth"] = ocs_df["ExpireMonth"].apply(lambda x: x[2:])
        # ocs_df["CallOrPut"] = ocs_df["Name"].apply(lambda x: "购" in x)
        ocs_df["CallOrPut"] = ocs_df["CallOrPut"].apply(lambda x: 708001000 == int(x))
        ocs_df["StatusDate"] = date
        return ocs_df

    def get_option_chain_symbol(self, underlying_code=None, date_list=None, reserve_modified=False):
        """
        获取期权合约属性
        :param underlying_code: 标的Wind代码，默认查询所有标的
        :param reserve_modified: 是否保留分红后的期权，默认不保留
        :return:
        """
        option_chain_symbol = pd.DataFrame(columns=['ModifiedSymbol', 'Name', 'Symbol', 'ExpireMonth',
                                                    'StrikePrice', 'StartTradingDate', 'LastTradingDate',
                                                    'ExercisingDate', 'DeliveryDate', 'AdjustSign', 'ContractCount',
                                                    'Underlying', 'CallOrPut', 'StatusDate'])
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        # TODO 日期可传字符串，列表
        if date_list is None:
            date_list = [self.today.strftime("%Y%m%d")]
        elif isinstance(date_list, int):
            date_list = [str(date_list)]
        elif isinstance(date_list, str):
            date_list = [date_list]
        elif isinstance(date_list, list):
            date_list = [str(i) for i in date_list]
        for i in date_list:
            assert is_valid_date(i, date_type="year_month_day"), "【date】默认为None，取当天的日期，或传8位字符的日期，如'20240416', 或日期列表"
        if underlying_code is None:
            sql1 = """select S_INFO_WINDCODE,S_INFO_CODE,S_INFO_NAME
                      from xquant_wind.chinaoptioncontpro 
                      """
        else:
            underlying_code_sql = self.__trans_params(underlying_code)
            sql1 = """select S_INFO_WINDCODE,S_INFO_CODE,S_INFO_NAME
                      from xquant_wind.chinaoptioncontpro 
                      where S_INFO_WINDCODE in {}
                      """.format(underlying_code_sql)
        contpro_df = dml.getAllByPandas(c_name, sql1)
        # 将仿真的期权代码数据过滤
        contpro_df["filter"] = contpro_df["S_INFO_NAME"].apply(lambda x: False if "仿真" in x else True)
        contpro_df = contpro_df[contpro_df["filter"]]
        if contpro_df.empty:
            dml.close(c_name)
            return option_chain_symbol
        sc_code = contpro_df["S_INFO_CODE"].values.tolist()
        contpro_df.rename(columns={"S_INFO_WINDCODE": "Underlying"}, inplace=True)
        sc_code_sql = self.__trans_params(sc_code)
        if not sc_code_sql:
            dml.close(c_name)
            return option_chain_symbol
        sql2 = """select S_INFO_EXCODE,S_INFO_EXNAME,S_INFO_WINDCODE,S_INFO_MONTH,S_INFO_STRIKEPRICE,
                         S_INFO_FTDATE,S_INFO_LASTTRADINGDATE,S_INFO_EXERCISINGEND,S_INFO_LDDATE,
                         ADJ_SIGN,S_INFO_COUNIT,S_INFO_SCCODE, S_INFO_CALLPUT
                         from xquant_wind.chinaoptiondescription 
                         where S_INFO_SCCODE in {}
                """.format(sc_code_sql)
        ocs = dml.getAllByPandas(c_name, sql2)
        for date in date_list:
            ocs_df = self.__process_data(ocs, contpro_df, date)
            ocs_df = ocs_df.sort_values(by=["ExpireMonth", "CallOrPut", "StrikePrice"])
            ocs_df = self.__restore_option_status_to_day(c_name, ocs_df, date)
            option_chain_symbol = pd.concat([option_chain_symbol, ocs_df])

        dml.close(c_name)
        if not reserve_modified:
            option_chain_symbol = option_chain_symbol[
                (option_chain_symbol["AdjustSign"] == "M") | (pd.isnull(option_chain_symbol["AdjustSign"]))]
        self.strikes = sorted(option_chain_symbol.StrikePrice.unique().tolist())
        self.contract_months = sorted(option_chain_symbol.ExpireMonth.unique().tolist())
        # 传日期列表后不能限制标的的唯一性了
        # assert option_chain_symbol["Symbol"].is_unique, "Non-Unique Symbol Appeared..."
        option_chain_symbol.reset_index(drop=True, inplace=True)
        return option_chain_symbol


if __name__ == '__main__':
    # pd.set_option("display.max_columns", None)
    import time

    t0 = time.time()
    op = OptionDataFP()
    df = op.get_option_chain_symbol("CU1904.SHF", date_list=['20190318', '20190319'])

    print("查询耗时：{}".format(time.time() - t0))
    print(df)
