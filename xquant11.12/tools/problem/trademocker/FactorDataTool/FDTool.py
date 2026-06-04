#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/3 15:32
import pandas as pd
from FactorDataTool.Config import MARKET_TYPE, INDEX_TYPE, INDUSTRY_TYPE
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SHENWAN_I_CODE, SHENWAN_II_CODE
from FactorDataTool.Config import LEVEL, LEVEL_MAP
from FactorDataTool.Config import HSET_HBASE_COLUMNS, CBOND_STOCK_HBASE_COLUMNS
from FactorDataTool.Config import INDEX_FUTURE_CODE, INDEX_FUTURE_HBASE_COLUMNS
from xquant.factordata import FactorData


class FDTool:
    def __init__(self, lib_name):
        self.lib_name = lib_name
        self.fa = FactorData()

    def hset(self, set_type, date, code):
        """  查询成分股
        set_type: 支持 "MAEKET", "INDEX"，"INDUSTRY"
        date: 交易日
        code: 代码, "MAEKET": ALLA， ALLA_HIS, "INDEX": HS300, ZZ500, SZ50，"INDUSTRY": 中信/申万一级/二级行业代码
        """
        assert set_type in ["MARKET", "INDEX", "INDUSTRY"], "ONLY SUPPORT MARKET, INDEX OR INDUSTRY"
        if set_type == "MARKET":
            assert code in MARKET_TYPE, "ONLY SUPPORT ALLA OR ALLA_HIS"
        elif set_type == "INDEX":
            assert code in INDEX_TYPE, "ONLY SUPPORT SZ50, HS300 AND ZZ500"
        elif set_type == "INDUSTRY":
            if code.endswith(".SI"):
                assert code in SHENWAN_I_CODE + SHENWAN_II_CODE, "ONLY SUPPORT SHENWAN I AND II"
            else:
                code = code.split(".")[1]   ### 去掉 CITICS. 和 SW.
                assert (code in CITICS_I_CODE + CITICS_II_CODE) or (code in SW_I_CODE + SW_II_CODE) , "ONLY SUPPORT CITICS OR SW LEVEL I OR II"
        try:
            stock_set = self.fa.get_factor_value(self.lib_name, "{}".format(code), "{}".format(date), HSET_HBASE_COLUMNS)
        except:
            stock_set = pd.DataFrame(columns=HSET_HBASE_COLUMNS)
        stock_set = stock_set[HSET_HBASE_COLUMNS[0]].tolist()
        return stock_set

    def hsi(self, stock, date, industry_type, industry_level):
        """ 获取股票所在行业信息
        stock: 股票或股票列表
        date: 交易日
        industry_type: ’CSRC’ 为证监会行业分类，’CITICS’ 为中信行业分类，’SW’ 为申万行业分类, 目前只支持CITICS和SW
        新增WIND中申万行业信息，行业代码与WIND客户端保持一致，以".SI"结尾
        industry_level: 1, 2, 3，目前只支持1, 2
        """
        assert industry_type in INDUSTRY_TYPE, "ONLY SUPPORT CITICS OR SW OR SHENWAN"
        assert industry_level in LEVEL, "ONLY SUPPORT LEVEL I OR II"
        hbase_columns = ["Stock"] + [industry_type + LEVEL_MAP[industry_level] + "Code"]

        if isinstance(stock, str):
            stock = [stock]
        try:
            stock_industry = self.fa.get_factor_value(self.lib_name, "{}".format(date), "20200102", hbase_columns)
        except:
            stock_industry = pd.DataFrame(columns=hbase_columns)
        stock_industry = stock_industry.reindex(columns=hbase_columns)
        stock_industry.columns = ["Stock", "IndustryCode"]
        if not stock_industry.empty:
            return stock_industry[stock_industry["Stock"].isin(stock)]
        else:
            return stock_industry

    def hsi_set(self, stock, date, industry_type, industry_level):
        """ 获取某个交易日和Stock处于同一行业的其他所有股票
        stock: 股票
        """
        stock_industry = self.hsi(stock, date, industry_type, industry_level)["IndustryCode"].values[0]
        indus_code = industry_type + "." + stock_industry
        stock_set = self.hset("INDUSTRY", date, indus_code)
        stock_set.remove(stock)
        return stock_set

    def cbs_map(self, date, code=None, code_type="CBOND"):
        """ 获取转债和正股对应关系，输入code_list为转债或正股，返回为{CBond: Stock}字典
        """
        hbase_columns = CBOND_STOCK_HBASE_COLUMNS

        if isinstance(code, str):
            code = [code]
        try:
            cbond_stock_df = self.fa.get_factor_value(self.lib_name, "{}".format(date), "20200102", hbase_columns)
        except:
            cbond_stock_df = pd.DataFrame(columns=hbase_columns)
        cbond_stock_df = cbond_stock_df.reindex(columns=hbase_columns)
        cbond_stock_df.columns = ["CBond", "Stock"]

        if code is None:
            return cbond_stock_df

        if not cbond_stock_df.empty:
            if code_type == "CBOND":
                cbond_stock_df = cbond_stock_df[cbond_stock_df["CBond"].isin(code)]
            elif code_type == "STOCK":
                cbond_stock_df = cbond_stock_df[cbond_stock_df["Stock"].isin(code)]
        return cbond_stock_df

    def get_future_contract(self, date, code, contract_type="ALL"):
        """ 获取某个交易日的期货合约代码
            contract_type, ZL00: 主力合约，ZL01: 次主力合约，ALL: 所有合约
        """
        assert code in INDEX_FUTURE_CODE, " Index Future Code Type Only Support IF, IC, IH"
        assert contract_type in ["ZL00", "ZL01", "ALL"], "Contract Type Only Support ZL00, ZL01 OR ALL"

        code_hbase = "{}_IdF".format(code)
        hbase_columns = INDEX_FUTURE_HBASE_COLUMNS
        try:
            index_future_set = self.fa.get_factor_value(self.lib_name, "{}".format(code_hbase), "{}".format(date), hbase_columns)
        except:
            index_future_set = pd.DataFrame(columns=hbase_columns)
        index_future_set = index_future_set.reindex(columns=hbase_columns)
        index_future_set.columns = ["ZL00", "ZL01", "ALL"]
        idf_contract_list = index_future_set[contract_type].tolist()
        if len(idf_contract_list) == 0:
            if contract_type in ["ZL00", "ZL01"]:
                return None
            else:
                return []
        return idf_contract_list[0]


if __name__ == "__main__":
    lib_name = "FutureDataLib"
    set_type = "INDUSTRY"
    date = "20200805"
    code = "801011.SI"
    instance = FDTool(lib_name)
    stock_set = instance.hset(set_type, date, code)
    stock = "000001.SZ"
    stock_hsi = instance.hsi(stock, date, industry_type="SHENWAN", industry_level=2)
    future = "IF"
    index_future_set = instance.get_future_contract(date, future, "ZL00")
    print(index_future_set)
