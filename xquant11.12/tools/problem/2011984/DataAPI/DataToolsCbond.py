"""可转债数据函数"""
import pandas as pd
from xquant.factordata import FactorData


fa = FactorData()


def cbond_set(date, set_type="ALL"):
    """
    :param date: 日期
    :param set_type: ALL：当天所有可交易的可转债代码，ALL_HIS: 历史上所有的可转债代码
    """
    # 获取所有沪深市场中可转债代码
    all_cbond_list = fa.get_factor_value("WIND_CCBondIssuance", factors=["S_INFO_WINDCODE"], S_INFO_WINDCODE="like'%.S%'",
                                         IS_CONVERTIBLE_BONDS="1")["S_INFO_WINDCODE"].tolist()

    if set_type == "ALL":
        # 获取当天所有转债代码
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


def get_cbond_stock_map(code_list, code_type="CBOND"):
    """ 注意存在同一个正股，同一个COMPCODE对应多个CBOND的情况，比如：113020.SH, 113032.SH, 对应 601233.SH
        返回键值为CBond，值为STOCK的字典
    """
    if isinstance(code_list, str):
        code_list = [code_list]
    if len(code_list) == 0:
        return {}
    code_list = list(set(code_list))
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
    else:
        raise ValueError

    cbond_stock_info = pd.merge(stock_info, cbond_info, on="COMPCODE", how="outer")
    cbond_stock_map = cbond_stock_info[["CBOND", "STOCK"]].set_index("CBOND")["STOCK"].to_dict()
    # 剔除CBond为NaN键值对
    cbond_stock_map = {cb: stock for cb, stock in cbond_stock_map.items() if isinstance(cb, str) and
                       (cb.endswith(".SH") or cb.endswith(".SZ"))}
    return cbond_stock_map


def get_cb_premium_ratio(code_list, date, lookback=120):
    """获取过去一段时间区间正股和可转债价格比例"""
    if isinstance(code_list, str):
        code_list = [code_list]
    end_date = str(date)
    date_list = sorted(fa.tradingday(end_date, -lookback))

    ### 获取可转债的转股价格
    conv_price = fa.get_factor_value("WIND_CBondConvPrice",
                                     factors=["S_INFO_WINDCODE", "S_INFO_ENDDATE", "CB_ANAL_CONVPRICE"],
                                     S_INFO_WINDCODE=code_list)
    conv_price = conv_price.set_index(["S_INFO_ENDDATE", "S_INFO_WINDCODE"])
    conv_price = conv_price["CB_ANAL_CONVPRICE"].unstack()

    ### 获取转债对应正股
    cb_stock_map = get_cbond_stock_map(code_list, code_type="CBOND")
    stock_list = list(cb_stock_map.values())

    stock_price = fa.get_factor_value("Basic_factor", stock=stock_list, mddate=date_list, factor_names=["close", "trade_status"])
    stock_price = stock_price["close"].unstack()

    conv_price_fill = pd.DataFrame(index=stock_price.index, columns=conv_price.columns)
    for date in conv_price_fill.index:
        conv_price_fill.loc[date] = conv_price.loc[:date].fillna(method='ffill').iloc[-1].values

    price_ratio = pd.DataFrame(index=stock_price.index, columns=conv_price.columns)
    ### 存在不同转债对应同一个正股的情况，导致正股数据少一些列
    for cb in price_ratio.columns:
        stock = cb_stock_map.get(cb)
        price_ratio.loc[:, cb] = stock_price.loc[:, stock] / conv_price_fill.loc[:, cb]

    return price_ratio
