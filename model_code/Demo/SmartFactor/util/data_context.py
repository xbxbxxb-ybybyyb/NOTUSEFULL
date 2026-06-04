from xquant.factordata import FactorData

s = FactorData()



def get_before_trade_days(day, bf_num):
    """
    获取交易日之前N个交易日
    :param day:
    :param bf_num:
    :return:
    """
    # from tquant.basic_data import BasicData
    # bd = BasicData()
    # trading_days = bd.get_trading_day(day, -bf_num)
    trading_days = s.tradingday(day, -bf_num)
    return trading_days


def get_before_trade_day(day, bf_num):
    """
    获取交易日之前N个交易日
    :param day:
    :param bf_num: 0 返回当天 1 返回前一个交易日 以此类推
    :return:
    """
    # from tquant.basic_data import BasicData
    # bd = BasicData()
    # trading_days = bd.get_trading_day(day, -(bf_num+1))
    trading_days = s.tradingday(day, -(bf_num + 1))
    return trading_days[0]


def get_trade_days(dt_from, dt_to):
    # from tquant.basic_data import BasicData
    # bd = BasicData()
    # return bd.get_trading_day(dt_from, dt_to)
    return s.tradingday(dt_from, dt_to)


# 支持两种模式：如果不传end_date,就返回开始日期前quarter_lag个报告期list
#               如果传 end_date, 就返回从开始日期前第quarter_lag个报告期到结束日期前一个报告期的list
def get_before_report_day(start_date, quarter_lag, end_date=None):
    date_list_complete = ['20000331', '20000630', '20000930', '20001231', '20010331', '20010630', '20010930',
                          '20011231',
                          '20020331', '20020630', '20020930', '20021231', '20030331', '20030630', '20030930',
                          '20031231',
                          '20040331', '20040630', '20040930', '20041231', '20050331', '20050630', '20050930',
                          '20051231',
                          '20060331', '20060630', '20060930', '20061231', '20070331', '20070630', '20070930',
                          '20071231',
                          '20080331', '20080630', '20080930', '20081231', '20090331', '20090630', '20090930',
                          '20091231',
                          '20100331', '20100630', '20100930', '20101231', '20110331', '20110630', '20110930',
                          '20111231',
                          '20120331', '20120630', '20120930', '20121231', '20130331', '20130630', '20130930',
                          '20131231',
                          '20140331', '20140630', '20140930', '20141231', '20150331', '20150630', '20150930',
                          '20151231',
                          '20160331', '20160630', '20160930', '20161231', '20170331', '20170630', '20170930',
                          '20171231',
                          '20180331', '20180630', '20180930', '20181231', '20190331', '20190630', '20190930',
                          '20191231',
                          '20200331', '20200630', '20200930', '20201231', '20210331', '20210630', '20210930',
                          '20211231',
                          '20220331', '20220630', '20220930', '20221231', '20230331', '20230630', '20230930',
                          '20231231',
                          '20240331', '20240630', '20240930', '20241231', '20250331', '20250630', '20250930',
                          '20251231',
                          '20260331', '20260630', '20260930', '20261231', '20270331', '20270630', '20270930',
                          '20271231',
                          '20280331', '20280630', '20280930', '20281231', '20290331', '20290630', '20290930',
                          '20291231',
                          '20300331', '20300630', '20300930', '20301231', '20310331', '20310630', '20310930',
                          '20311231']
    qtr_list = [str(i) for i in date_list_complete if i <= start_date][-1 * quarter_lag:]
    if end_date:
        qtr_tmp = []
        for i in date_list_complete:
            if i < start_date:
                continue
            elif start_date <= i <= end_date:
                qtr_tmp.append(i)
            else:
                break
        qtr_list += qtr_tmp
    return qtr_list


def get_factor(date_list, fac_names=None, stocks=None):
    """
    多因子多天多股票

    :param date_list:
    :param fac_names:
    :param stocks
    :return:
    """
    # from tquant.stock_data import StockData
    # sd = StockData()
    # df2_1 = sd.get_factor_price_daily(stocks, date_list, fac_names, fill_na=True)
    df2_1 = s.get_factor_value("Basic_factor", stocks, date_list, fac_names, fill_na=True)
    return df2_1


def get_stocks_pool(day, security_type, securities="alpha_universe"):
    """
    获取股票池
    :return:
    """
    # from tquant.index_data import IndexData
    # from tquant.stock_data import StockData
    day = get_before_trade_day(day, 0)
    if securities == "alpha_universe":
        securities = "ALLA_HIS"
    if isinstance(securities, str):
        # 目前支持 'ALLA', 'SHA', 'SZA', 'ALLA_HIS', 'HS300','ZZ500','SH50'
        securities = securities.upper()
        if security_type == 'stock' and securities in ['ALLA', 'SHA', 'SZA', 'ALLA_HIS']:
            # sd = StockData()
            # res = sd.get_plate_info('MARKET', day, securities)['stock'].tolist()
            res = s.hset('MARKET', day, securities)['stock'].tolist()

        elif security_type == 'stock' and securities.upper() in ['HS300', 'ZZ500', 'SH50', 'SZ50', 'ZZ800', 'ZZ1000']:
            # ind = IndexData()
            # res = ind.get_index_info(day, securities, 0)['stock'].tolist()
            res = s.hset('INDEX', day, securities, 0)['stock'].tolist()
        else:
            raise Exception("证券类型{} 暂不支持传入{} 类型的标的池参数".format(security_type, securities))
        if not res:
            raise Exception("日期：{0} 中 证券类型为{1}的标的池为空".format(day, security_type))
        return res
    elif isinstance(securities, list):
        return securities
    else:
        raise Exception("暂不支持传入该类型的securities: {}!".format(securities))

# def get_factor_lib(factor_list):
#     from tquant.stock_data import StockData
#     sd = StockData()
#     factor_lib = sd.get_factor_lib(factor_list)
#     return factor_lib[0]
