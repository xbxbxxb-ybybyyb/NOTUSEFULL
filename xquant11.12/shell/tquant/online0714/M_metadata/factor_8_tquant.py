import pandas as pd
from metadata import MetaData

md = MetaData()


# {目录名:[表名，{因子：因子名称}]}
def get_table_factor(file_name="factors_sql_config.xlsx"):
    data = pd.read_excel(file_name, sheet_name=None, header=0, usecols=["因子名称", "因子中文名", "目的表", "是否已存在"])
    df_list = []
    for key in list(data.keys()):
        df_list.append(data[key])
    table_dict = {"factor_d_financialanalysisindex_PART5": "factor_day_financialanalysisindex_part5",
                  "factor_day_financialanalysisindex_PART5":"factor_day_financialanalysisindex_part5",
                  "factor_d_financialreportindex_part1": "factor_day_financialreportindex",
                  "factor_d_financialanalysisindex_part3": "factor_day_financialanalysisindex_part3",
                  "factor_d_financialanalysisindex_part2": "factor_day_financialanalysisindex_part2",
                  "factor_d_financialanalysisindex_PART4": "factor_day_financialanalysisindex_part4",
                  "factor_d_financialanalysisindex_part1": "factor_day_financialanalysisindex_part1",
                  "factor_d_financialanalysisindex_part4": "factor_day_financialanalysisindex_part4",
                  "factor_d_valuationmetricsindex": "factor_day_valuationmetricsindex",
                  "factor_d_riskanalysisindex": "factor_day_riskanalysisindex",
                  "factor_d_financialreportindex": "factor_day_financialreportindex", }
    f = lambda x: table_dict[x] if x in table_dict.keys() else x
    f2 = lambda x: x.lower()
    df = pd.concat(df_list)
    df.rename(columns={"因子名称": "factor", "因子中文名": "factor_name", "目的表": "table", "是否已存在": "isvalid"}, inplace=True)
    df["isvalid"] = df["isvalid"].apply(lambda x: x.upper())
    df = df[(~df["table"].isnull()) & (df["isvalid"] == "Y")]
    df.drop("isvalid", axis=1, inplace=True)
    df = df.applymap(f)
    df = df.applymap(f2)
    df.set_index("table", inplace=True)
    df["factor"] = df["factor"].apply(str)
    df["factor"] = df["factor"].apply(lambda x: x.strip().lower())

    # ----------------------------------------
    # factor_count = dict(df["factor"].value_counts())
    # for i in factor_count:
    #     if factor_count[i] > 1:
    #         print(df[df["factor"] == i])
    # -----------------------------------------
    # df.to_csv("entered.csv", encoding='utf_8_sig')
    factor_dict = {}
    table_names = list(set(df.index.values))
    table_names = [i.lower() for i in table_names]

    for table_name in table_names:
        df_p = df.loc[table_name, :]
        if isinstance(df_p, pd.Series):
            df_p = pd.DataFrame(df_p).T
        df_p.reset_index(drop=True, inplace=True)
        df_p.set_index("factor", inplace=True)
        df_p_dict = df_p.to_dict(orient='dict')
        factor_dict[table_name] = df_p_dict["factor_name"]
    return factor_dict


def get_catalog_factor(cata_name):
    # 获取目录与因子的关联关系
    catalog_table = {"行情指标": ["factor_day_marketindex"], "估值指标": ["factor_day_valuationmetricsindex"],
                     "财务报表": ["factor_day_financialreportindex", "factor_day_issuingdateindex"],
                     "财务分析": ["factor_day_financialanalysisindex_part1", "factor_day_financialanalysisindex_part2",
                              "factor_day_financialanalysisindex_part3", "factor_day_financialanalysisindex_part4",
                              "factor_day_financialanalysisindex_part5"],
                     "风险分析": ["factor_day_riskanalysisindex"],
                     "分红指标": ["factor_day_dividendindex"],
                     "最新信息": ["factor_day_newmsgindex"],
                     "Alpha指标": ["factor_day_alpha191_part1", "factor_day_alpha191_part2"],
                     "Barra指标": ["factor_day_barra"],
                     "技术面指标": ["factor_day_technicalanalysis"],
                     "动量指标": ["factor_day_momentum"], "情绪指标": ["factor_day_emotion"]}
    table_factor_dict = get_table_factor()
    catalog_factor = []
    for table in table_factor_dict.keys():
        if table in catalog_table[cata_name]:
            catalog_factor.extend(list(table_factor_dict[table].keys()))
    return catalog_factor


if __name__ == "__main__":
    library_name = "Basic_factordata"
    # #1. 新增库
    # md.add_factor_library("Basic_factordata")

    # # 2. 新建因子目录
    # catalog_dict = {"行情指标": 2, "估值指标": 3, "财务报表": 4, "分红指标": 5,
    #                 "最新信息": 6, "一致预期": 7, "财务分析": 8, "风险分析": 9,
    #                 "Alpha指标": 10, "Barra指标": 11, "技术面指标": 12,
    #                 "动量指标": 13, "情绪指标": 14,}

    # for cata_name in catalog_dict:
    #     md.add_factor_catalog("Basic_factordata", cata_name, catalog_dict[cata_name])

    # # 3.新增因子查询配置 library_name, factor_dict, data_frequency, owner_table_name
    # table_factor_dict = get_table_factor()
    # tables = ['factor_day_riskanalysisindex', 'factor_day_marketindex', 'factor_day_financialanalysisindex_part3',
    #           'factor_day_financialanalysisindex_part1', 'factor_day_financialanalysisindex_part2',
    #           'factor_day_financialanalysisindex_part4', 'factor_day_valuationmetricsindex',
    #           'factor_day_financialreportindex', 'factor_day_financialanalysisindex_part5',
    #           'factor_day_dividendindex', 'factor_day_newmsgindex', "factor_day_alpha191_part1",
    #           "factor_day_alpha191_part2", "factor_day_barra", "factor_day_technicalanalysis",
    #           "factor_day_momentum", "factor_day_emotion", "factor_day_issuingdateindex"]
    # for table in tables:
    #     try:
    #         md.add_factor_meta("Basic_factordata", table_factor_dict[table], 6,table)
    #     except Exception as e:
    #         print("table:{0} insert error,the reason:{1}".format(table,e))
    # # md.add_factor_meta("Basic_factordata", table_factor_dict["factor_day_issuingdateindex"], 6, "factor_day_issuingdateindex")

    # 一致预期
    # from conforecastindex_factor import get_conforecastindex_factor_info
    # factors_info = get_conforecastindex_factor_info()
    # for table in factors_info.keys():
    #     print(table)
    #     md.add_factor_meta("Basic_factordata", factors_info[table], 6, table)




    # 4. 新增因子与目录关联 library_name, cata_name, factor_list
    catalog_list = ["行情指标", "估值指标", "财务报表", "财务分析", "风险分析", "最新信息",
                    "Alpha指标", "Barra指标", "技术面指标", "动量指标", "情绪指标"]#, "分红指标"
    for cata_name in catalog_list:
        try:
            md.add_factor_catalog_rela("Basic_factordata", cata_name, get_catalog_factor(cata_name))
        except Exception as e:
            print("<ERROR> : table:{0} insert error,the reason:{1}".format(cata_name, e))

    # md.add_factor_catalog_rela("Basic_factordata", "财务报表", get_catalog_factor("财务报表"))

    # # 一致预期
    # from conforecastindex_factor import get_conforecastindex_factor_info
    # factors_info = get_conforecastindex_factor_info()
    # factor_list = []
    # for table in factors_info.keys():
    #     factors = list(factors_info[table].keys())
    #     factor_list.extend(factors)
    # print(len(factor_list))
    # md.add_factor_catalog_rela("Basic_factordata", "一致预期", factor_list)

