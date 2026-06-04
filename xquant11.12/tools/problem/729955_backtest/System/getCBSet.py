from xquant.factordata import FactorData

fa = FactorData()


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