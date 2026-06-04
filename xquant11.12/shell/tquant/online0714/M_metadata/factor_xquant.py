
import pandas as pd
from metadata import MetaData

md = MetaData()


if __name__ == "__main__":
    # # 新增因子查询配置 library_name, factor_dict, data_frequency, owner_table_name
    # 20201120
    # # 1.
    # factor_dict = {"sec_status": "证券存续状态", "sec_name": "证券简称"}
    # md.add_factor_meta("Basic_factor", factor_dict, 6, "factor_d_newmsgindex")
    # print("sec_status,sec_name add_factor_meta seccess !")
    #
    # # 新增因子与目录关联 library_name, cata_name, factor_list
    # factor_list = ["sec_status", "sec_name"]
    # md.add_factor_catalog_rela("Basic_factor", "最新信息", factor_list)
    # print("sec_status,sec_name add_factor_catalog_rela seccess !")

    # 一、财务报表--业绩快报7个因子
    factor_dict = {"ann_dt_kb": "公告日期（业绩快报）", "yoysales_kb":"同比增长率:营业收入", "yoyop_kb":"同比增长率:营业利润",
                   "yoyebt_kb":"同比增长率:利润总额", "yoynetprofit_deducted_kb":"同比增长率:归属母公司股东的净利润",
                   "yoyeps_basic_kb":"同比增长率:基本每股收益", "roe_yearly_kb":"同比增减:加权平均净资产收益率"}
    md.add_factor_meta("Basic_factor", factor_dict, 6, "factor_d_profitnotice")
    print("add_factor_meta seccess !")
    #
    # # 新增因子与目录关联 library_name, cata_name, factor_list
    # factor_list = ["ann_dt_kb", "yoysales_kb", "yoyop_kb", "yoyebt_kb", "yoynetprofit_deducted_kb",
    #                "yoyeps_basic_kb", "roe_yearly_kb"]
    # md.add_factor_catalog_rela("Basic_factor", "财务报表", factor_list)
    # print("mdc_trade_status add_factor_catalog_rela seccess !")

    # 二、财务报表--利润表新增1个因子
    # factor_dict = {"stmnote_finexp":"财务费用:利息费用"}
    # md.add_factor_meta("Basic_factor", factor_dict, 6, "factor_d_financialreportindex")
    # print("add_factor_meta seccess !")
    #
    # # 新增因子与目录关联 library_name, cata_name, factor_list
    # factor_list = ["stmnote_finexp"]
    # md.add_factor_catalog_rela("Basic_factor", "财务报表", factor_list)
    # print("mdc_trade_status add_factor_catalog_rela seccess !")

    # 三、财务分析--新增2个因子
    # factor_dict = {"ebit_fa":"息税前利润", "ebitda_fa":"息税折旧摊销前利润"}
    # md.add_factor_meta("Basic_factor", factor_dict, 6, "factor_d_financialanalysisindex")
    # print("add_factor_meta seccess !")
    #
    # # 新增因子与目录关联 library_name, cata_name, factor_list
    # factor_list = ["ebit_fa", "ebitda_fa"]
    # md.add_factor_catalog_rela("Basic_factor", "财务分析", factor_list)
    # print("mdc_trade_status add_factor_catalog_rela seccess !")

