from Constants.INDEX_LIST import INDEX_LIST, SHENWAN_INDEX_LIST, THIRD_INDEX_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from Constants.FUTURE_LIST import is_future_code, get_future_contract_type
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SHENWAN_I_CODE, SHENWAN_II_CODE
from Utils.TradingDay import getTradingDay, getNDaysOff

import pandas as pd
from xquant.factordata import FactorData
fa = FactorData()


def get_trading_day(start_date, end_date):
    if not isinstance(start_date, int):
        start_date = int(start_date)
    if not isinstance(end_date, int):
        end_date = int(end_date)
    trade_dates = getTradingDay(start_date, end_date)
    if len(trade_dates) == 0:
        return []
    else:
        trade_dates = sorted(list(map(lambda date_int: str(date_int), trade_dates)))
    return trade_dates

def get_ndays_offset(start_date, offset=0):
    if not isinstance(start_date, int):
        start_date = int(start_date)
    start_date_offset = str(getNDaysOff(start_date, offset))
    return start_date_offset

def get_code_type(code):
    if code in INDEX_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST:
        return 'INDEX'
    elif is_cbond_code(code):
        return "CBOND"
    elif code in ETF_LIST:
        return "ETF"
    elif code in LOF_LIST:
        return "LOF"
    elif code in CITICS_I_CODE + CITICS_II_CODE + SW_I_CODE + SW_II_CODE + SHENWAN_I_CODE + SHENWAN_II_CODE:
        return "INDUSTRY"
    elif is_future_code(code):
        return "FUTURE"
    else:
        return "STOCK"
    # else:
    #     raise Exception("Not Supported Type Yet: {}".format(code))

def is_cbond_code(code):
    if code.endswith(".SH"):
        if code.startswith("100") or code.startswith("110") or code.startswith("113"):
            return True
    elif code.endswith(".SZ"):
        if code.startswith("12") or code == "117103.SZ":
            return True
    return False

def get_industry_type(industry_code):
    if industry_code in CITICS_I_CODE + CITICS_II_CODE:
        return "CITICS"
    elif industry_code in SW_I_CODE + SW_II_CODE:
        return "SW"
    elif industry_code in SHENWAN_I_CODE + SHENWAN_II_CODE:
        return "SHENWAN"
    else:
        raise Exception("NOT Supported Industry Code: {}".format(industry_code))

def get_index_type(index_code):
    assert index_code in INDEX_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST, "NOT Supported Index Code: {}".format(index_code)
    if index_code in SHENWAN_INDEX_LIST:
        return "SHENWAN"
    elif index_code in THIRD_INDEX_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST:
        return "THIRD"
    else:
        return "ZZ"

def get_stock_list(date, list_type=""):
    date = "{}".format(date)
    pre_day = fa.tradingday(date, -2)[0]
    if list_type == "":
        stock_list = fa.hset('MARKET', pre_day, "ALLA")["stock"].tolist()
    elif list_type == "HIS":
        stock_list = fa.hset('MARKET', pre_day, "ALLA_HIS")["stock"].tolist()
    else:
        raise Exception("Not Supported Type Yet: {}".format(list_type))
    return stock_list

def get_cbond_list(date):
    from xquant.bonddata import BondData
    bd = BondData()

    bond_list = bd.get_bond_set(date, 'kzz')
    bond_list = [c for c in bond_list if c.endswith(".SH") or c.endswith(".SZ")]
    return bond_list

def get_fund_list(date, fund_type="ETF"):
    from xquant.funddata import FundData
    fd = FundData()

    if fund_type == "ETF":
        fund_list = fd.get_fund_set(date, "ETF")
    elif fund_type == "LOF":
        fund_list = fd.get_fund_set(date, "LOF")
    fund_list = [f for f in fund_list if f.endswith(".SH") or f.endswith(".SZ")]
    return fund_list

def get_index_future_list(start_date, end_date, zl_future_list=["IF"]):
    from xquant.futuredata import FutureData
    fd = FutureData()

    assert len(zl_future_list) > 0, " Main Contract List Empty"

    future_contract_list = []
    for zl_future in zl_future_list:
        contracts = fd.get_instrument_all(zl_future, start_date, end_date)
        future_contract_list.extend(contracts)

    all_future_contract = list(set(future_contract_list))
    if len(all_future_contract) > 0:
        all_future_contract = sorted(all_future_contract)

    return all_future_contract

def get_cbond_stock_map(code_list, code_type="CBOND"):
    """ 注意存在同一个正股，同一个COMPCODE对应多个CBOND的情况，比如：113020.SH, 113032.SH, 对应 601233.SH
        返回键值为CBond，值为 STOCK的字典
    """
    if isinstance(code_list, str):
        code_list = [code_list]

    if code_type == "STOCK":
        stock_info = fa.get_factor_value("WIND_AShareDescription", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_WINDCODE=code_list)
        stock_info.columns = ["STOCK", "COMPCODE"]
        s_info_compcode = stock_info["COMPCODE"].tolist()

        cbond_info = fa.get_factor_value("WIND_CCBondIssuance", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_COMPCODE=s_info_compcode, IS_CONVERTIBLE_BONDS="1")
        if cbond_info.empty:
            cbond_info = pd.DataFrame(columns=["CBOND", "COMPCODE"])
        cbond_info.columns = ["CBOND", "COMPCODE"]

    elif code_type == "CBOND":
        cbond_info = fa.get_factor_value("WIND_CCBondIssuance", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_WINDCODE=code_list, IS_CONVERTIBLE_BONDS="1")
        cbond_info.columns = ["CBOND", "COMPCODE"]
        s_info_compcode = cbond_info["COMPCODE"].tolist()

        stock_info = fa.get_factor_value("WIND_AShareDescription", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_COMPCODE=s_info_compcode)
        if stock_info.empty:
            stock_info = pd.DataFrame(columns=["STOCK", "COMPCODE"])
        stock_info.columns = ["STOCK", "COMPCODE"]

    cbond_stock_info = pd.merge(stock_info, cbond_info, on="COMPCODE", how="outer")
    cbond_stock_map = cbond_stock_info[["CBOND", "STOCK"]].set_index("CBOND")["STOCK"].to_dict()
    ### 剔除CBond为NaN键值对
    cbond_stock_map = {cb: stock for cb, stock in cbond_stock_map.items() if isinstance(cb, str) and
                       (cb.endswith(".SH") or cb.endswith(".SZ"))}
    return cbond_stock_map


def cbond_set(date, set_type="ALL"):
    """
    :param date: 日期
    :param set_type: ALL：当天所有可交易的可转债代码，ALL_HIS: 历史上所有的可转债代码
    """
    ### 获取所有沪深市场中可转债代码
    all_cbond_list = fa.get_factor_value("WIND_CCBondIssuance", factors=["S_INFO_WINDCODE"], S_INFO_WINDCODE="like'%.S%'",
                        IS_CONVERTIBLE_BONDS="1")["S_INFO_WINDCODE"].tolist()

    if set_type == "ALL":
        ### 获取当天所有转债代码
        bond_list = fa.get_factor_value("WIND_CCBondValuation", factors=["S_INFO_WINDCODE"], TRADE_DT=["{}".format(date)],
                            S_INFO_WINDCODE="like'%.S%'")["S_INFO_WINDCODE"].tolist()
        cbond_list = list(set(bond_list).intersection(all_cbond_list))

        traded_cbond = fa.get_factor_value("WIND_CBondEODPrices", factors=["S_INFO_WINDCODE"], S_DQ_TRADESTATUS=["交易"],
                                           S_INFO_WINDCODE=cbond_list, TRADE_DT=[str(date)])["S_INFO_WINDCODE"].tolist()
        if len(traded_cbond) > 0:
            traded_cbond = sorted(traded_cbond)

        return traded_cbond

    elif set_type == "ALL_HIS":
        bond_list = fa.get_factor_value("WIND_CCBondValuation", factors=["S_INFO_WINDCODE"], TRADE_DT=["<={}".format(date)],
                            S_INFO_WINDCODE="like'%.S%'")["S_INFO_WINDCODE"].tolist()

        cbond_list = list(set(bond_list).intersection(all_cbond_list))

        if len(cbond_list) > 0:
            cbond_list = sorted(cbond_list)

        return cbond_list

def is_sz_code(code):
    if code.endswith(".SZ"):
        flag = True
    else:
        flag = False

    return flag

def split_calc_date_into_group(calc_date_list, max_date_num_per_task=20):
    # 按照天数将需要计算的时间段进行分组，例如，每20个交易日分一组
    group = []
    size = len(calc_date_list)
    from_index = 0
    while from_index < size:
        group.append(calc_date_list[from_index: min(size, from_index + max_date_num_per_task)])
        from_index += max_date_num_per_task
    return group


####################### below are unused functions
def get_trading_day_old(start_date, end_date):
    if not isinstance(start_date, str):
        start_date = str(start_date)
    if not isinstance(end_date, str):
        end_date = str(end_date)
    trade_dates = fa.tradingday(start_date, end_date)
    if len(trade_dates)==0:
        return []
    else:
        trade_dates = sorted(trade_dates)
    return trade_dates

def get_ndays_offset_old(start_date, offset=0):
    if not isinstance(start_date,str):
        start_date = str(start_date)
    start_date_offset = fa.tradingday(start_date, -(offset + 1))[0]
    return start_date_offset

def get_cbond_list_old(date):
    traded_cbond = fa.get_factor_value("WIND_CCBondValuation", TRADE_DT=["{}".format(date)],
                                       IS_CONVERTIBLE_BONDS="1")["S_INFO_WINDCODE"].tolist()
    traded_cbond = [c for c in traded_cbond if c.endswith(".SH") or c.endswith(".SZ")]
    return traded_cbond

def get_etf_list_old():
    etf_info = fa.get_factor_value("WIND_ChinaETFPchRedmList", factors=["S_INFO_WINDCODE"])
    etf_list = etf_info['S_INFO_WINDCODE'].dropna().unique().tolist()
    return etf_list


if __name__ == "__main__":
    start_date = "20200101"
    end_date = "20200804"
    zl_future_list = ["IF", "IC"]
    future_list = get_index_future_list(start_date, end_date, zl_future_list)
    print(future_list)


