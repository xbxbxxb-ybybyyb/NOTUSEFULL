from tquant.index_data import IndexData
from tquant.stock_data import StockData
from tquant.basic_data import BasicData

factype_to_facname = {
    'alpha': ['alpha1', 'alpha2', 'alpha3', 'alpha4', 'alpha5', 'alpha6', 'alpha7', 'alpha8', 'alpha9', 'alpha10',
              'alpha11', 'alpha12', 'alpha13', 'alpha14', 'alpha15', 'alpha16', 'alpha17', 'alpha18', 'alpha19',
              'alpha20', 'alpha21', 'alpha22', 'alpha23', 'alpha24', 'alpha25', 'alpha26', 'alpha27', 'alpha28',
              'alpha29', 'alpha31', 'alpha32', 'alpha33', 'alpha34', 'alpha35', 'alpha36', 'alpha37',
              'alpha38', 'alpha39', 'alpha40', 'alpha41', 'alpha42', 'alpha43', 'alpha44', 'alpha45', 'alpha46',
              'alpha47', 'alpha48', 'alpha49', 'alpha50', 'alpha51', 'alpha52', 'alpha53', 'alpha54', 'alpha55',
              'alpha56', 'alpha57', 'alpha58', 'alpha59', 'alpha60', 'alpha61', 'alpha62', 'alpha63', 'alpha64',
              'alpha65', 'alpha66', 'alpha67', 'alpha68', 'alpha69', 'alpha70', 'alpha71', 'alpha72', 'alpha73',
              'alpha74', 'alpha75', 'alpha76', 'alpha77', 'alpha78', 'alpha79', 'alpha80', 'alpha81', 'alpha82',
              'alpha83', 'alpha84', 'alpha85', 'alpha86', 'alpha87', 'alpha88', 'alpha89', 'alpha90', 'alpha91',
              'alpha92', 'alpha93', 'alpha94', 'alpha95', 'alpha96', 'alpha97', 'alpha98', 'alpha99', 'alpha100',
              'alpha101', 'alpha102', 'alpha103', 'alpha104', 'alpha105', 'alpha106', 'alpha107', 'alpha108',
              'alpha109', 'alpha110', 'alpha111', 'alpha112', 'alpha113', 'alpha114', 'alpha115', 'alpha116',
              'alpha117', 'alpha118', 'alpha119', 'alpha120', 'alpha121', 'alpha122', 'alpha123', 'alpha124',
              'alpha125', 'alpha126', 'alpha127', 'alpha128', 'alpha129', 'alpha130', 'alpha131', 'alpha132',
              'alpha133', 'alpha134', 'alpha135', 'alpha136', 'alpha137', 'alpha138', 'alpha139', 'alpha140',
              'alpha141', 'alpha142', 'alpha143', 'alpha144', 'alpha145', 'alpha146', 'alpha147', 'alpha148',
              'alpha149', 'alpha150', 'alpha151', 'alpha152', 'alpha153', 'alpha154', 'alpha155', 'alpha156',
              'alpha157', 'alpha158', 'alpha159', 'alpha160', 'alpha161', 'alpha162', 'alpha163', 'alpha164',
              'alpha165', 'alpha166', 'alpha167', 'alpha168', 'alpha169', 'alpha170', 'alpha171', 'alpha172',
              'alpha173', 'alpha174', 'alpha175', 'alpha176', 'alpha177', 'alpha178', 'alpha179', 'alpha180',
              'alpha181', 'alpha182', 'alpha183', 'alpha184', 'alpha185', 'alpha186', 'alpha187', 'alpha188',
              'alpha189', 'alpha190', 'alpha191'],
    'barra_cne5': ['barra_cne5_beta', 'barra_cne5_bp', 'barra_cne5_earningsyield_cetop',
                   'barra_cne5_earningsyield_epibs', 'barra_cne5_earningsyield_etop', 'barra_cne5_growth_egibs',
                   'barra_cne5_growth_egibs_s', 'barra_cne5_growth_egro', 'barra_cne5_growth_sgro', 'barra_cne5_halpha',
                   'barra_cne5_leverage_blev', 'barra_cne5_leverage_dtoa', 'barra_cne5_leverage_mlev',
                   'barra_cne5_liquidity_stoa', 'barra_cne5_liquidity_stom', 'barra_cne5_liquidity_stoq',
                   'barra_cne5_residualvolatility_cmra', 'barra_cne5_residualvolatility_dastd',
                   'barra_cne5_residualvolatility_hsigma', 'barra_cne5_rstr', 'barra_cne5_size'],
    'emotion': ['cv_turn', 'relative_vol_updown'],
    'financialanalysis': ['apturn', 'apturndays', 'growth_cagr_netprofit_3y', 'growth_cagr_netprofit_5y',
                          'growth_cagr_tr_3y', 'growth_cagr_tr_5y', 'maintenance', 'netturndays',
                          'non_currentassetsturn', 'operatecapitalturn', 'yoycf', 'yoydebt', 'yoyprofit', 'yoy_assets',
                          'yoy_cash', 'yoy_fixedassets'],
    'momentum': ['halpha', 'relative_strength_12m', 'relative_strength_1m', 'relative_strength_2m',
                 'relative_strength_3m', 'relative_strength_6m', 'weighted_strength_12m', 'weighted_strength_2m',
                 'weighted_strength_3m'],
    'technicalanalysis': ['close1', 'close12', 'close2', 'close3', 'close6', 'coskew', 'ema_crossover',
                          'isabove_avg_mon', 'ln_close', 'long_bear', 'long_bull', 'mktcapfloat', 'negskew',
                          'price_vol_corr', 'short_bear', 'short_bull', 'std1', 'std12', 'std2', 'std3', 'std6', 'tr',
                          'tskew', 'turnover_m_ave1', 'turnover_m_ave12', 'turnover_m_ave2', 'turnover_m_ave3',
                          'turnover_m_ave6', 'turnover_m_ave_float1', 'turnover_m_ave_float12', 'turnover_m_ave_float2',
                          'turnover_m_ave_float3', 'turnover_m_ave_float6', 'turnover_w_ave', 'turnover_w_ave_float',
                          'vwap_close'],
    'valuationmetric': ['lncap_barra']
}


# 改造成从配置文件读取因子名
def get_fac_names(fac_type):
    """
    根据因子类获取因子名
    :param fac_type:
    :return:
    """
    all_type = list(factype_to_facname.keys())
    if isinstance(fac_type, str):
        if fac_type == 'all':
            fac_type = all_type
        else:
            fac_type = [fac_type]
    for i in fac_type:
        if i not in all_type and i != 'all':
            raise Exception('无此因子类,请重新输入')
    factor_names = []
    for i in fac_type:
        factor_names += factype_to_facname[i]

    return factor_names


def get_before_trade_days(day, bf_num):
    """
    获取交易日之前N个交易日
    :param day:
    :param bf_num:
    :return:
    """
    bd = BasicData()
    trading_days = bd.get_trading_day(day, -bf_num)
    return trading_days


def get_before_trade_day(day, bf_num):
    """
    获取交易日之前N个交易日
    :param day:
    :param bf_num:
    :return:
    """
    bd = BasicData()
    trading_days = bd.get_trading_day(day, -bf_num)
    return trading_days[0]


def get_trade_days(dt_from, dt_to):
    bd = BasicData()
    return bd.get_trading_day(dt_from, dt_to)


def get_before_report_day(date, quarter_lag):
    date = int(date)
    if quarter_lag == 0:
        raise Exception("quarter_lag 不支持传0 如果没有使用到，保持None值即可")
    if date < 20090105:
        last_day = 20090105
    else:
        last_day = date
    year_list = [str(i) for i in range(2000, 2100)]
    month_date = ['0331', '0630', '0930', '1231']
    date_list_complete = [i + j for i in year_list for j in month_date]
    qtr_list = [int(i) for i in date_list_complete if int(i) <= last_day][-1 * quarter_lag:]
    return qtr_list


def get_factor(date_list, fac_names=None, stocks=None):
    """
    多因子多天多股票

    :param date_list:
    :param fac_names:
    :param stocks
    :return:
    """
    sd = StockData()
    df2_1 = sd.get_factor_price_daily(stocks, date_list, fac_names, fill_na=True)
    return df2_1


def get_stocks_pool(day, security_type, securities="ALLA"):
    """
    获取股票池
    :return:
    """
    day = get_before_trade_day(day, -1)
    if isinstance(securities, str):
        #目前支持 'ALLA', 'SHA', 'SZA', 'ALLA_HIS', 'HS300','ZZ500','SH50'
        if security_type == 'stock' and securities in ['ALLA', 'SHA', 'SZA', 'ALLA_HIS']:
            sd = StockData()
            res = sd.get_plate_info('MARKET', day, securities)['stock'].tolist()

        elif security_type=='stock' and securities in ['HS300','ZZ500','SH50']:
            ind = IndexData()
            res = ind.get_index_info(day, securities, 0)['stock'].tolist()
        else:
            raise Exception("证券类型{} 暂不支持传入{} 类型的标的池参数".format(security_type,securities))
        return res
    elif isinstance(securities, list):
        return securities
    else:
        raise Exception("暂不支持传入该类型的securities: {}!".format(securities))
