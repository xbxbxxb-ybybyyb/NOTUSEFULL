def code_t(code_int):
    """转换股票代码，eg: 601318 转换为 601318.SH"""
    if len(str(code_int)) == 6:
        if str(code_int).startswith("6"):
            return "{}.SH".format(code_int)
        elif str(code_int).startswith("0") or str(code_int).startswith("3"):
            return "{}.SZ".format(code_int)
        else:  # 可转债
            if str(code_int).startswith("11"):
                return "{}.SH".format(code_int)
            elif str(code_int).startswith("12") or str(code_int).startswith("13"):
                return "{}.SZ".format(code_int)
    return "{}{}.SZ".format("0" * (6 - len(str(code_int))), code_int)


def code_name(code_list):
    """获取股票的中文名"""
    is_input_str = isinstance(code_list, str)
    if isinstance(code_list, str):
        code_list = [code_list]
    code_type = code_classify(code_list[0])
    from xquant.factordata import FactorData
    fa = FactorData()
    if code_type == 'stock':
        code_dict = fa.hset("MARKET", "20211008", "ALLA_HIS").set_index(['stock'])['stock_name'].to_dict()
    elif code_type == 'cb':
        code_dict = fa.get_factor_value('WIND_CBondDescription', factors=['S_INFO_WINDCODE', 'S_INFO_NAME'],
                                        S_INFO_WINDCODE="like'%.S%'").set_index('S_INFO_WINDCODE')['S_INFO_NAME'].to_dict()
    else:
        raise ValueError
    code_name = [code_dict[code] for code in code_list]
    if is_input_str:
        code_name = code_name[0]
    return code_name


def code_industry(code_list, base_date, industry_type='CITICS', level=1):
    """
    获取股票所属的行业
    industryType: 行业类型，’CSRC’ 为证监会行业分类，’CITICS’ 为中信行业分类，’SW’ 为申万行业分类，默认全部行业。
    level:行业级别，取值[1,3]之间的整数，默认为三级行业，证监会行业只有两级分类取[1,2]的整数
    """
    from xquant.factordata import FactorData

    fa = FactorData()
    industry = fa.hsi(code_list, base_date, industryType=industry_type, industryLevel=level)
    industry_dict = industry.set_index('stock')['industry_name'].to_dict()
    return industry_dict


def get_code_status(code_list, trade_date):
    from xquant.factordata import FactorData
    if isinstance(code_list, str):
        code_list = [code_list]
    if code_list[0].startswith('1'):  # 转债
        status = {}
        for code in code_list:
            status_code = FactorData().get_factor_value("ZeusDataLib", code, '20200102', ['D_Date', 'D_TradeStatus']).set_index('D_Date')
            status.update({code: status_code.loc[trade_date, 'D_TradeStatus']})
    else:
        status = FactorData().get_factor_value("Basic_factor", code_list, [trade_date], ["trade_status"])
        if status.empty:
            return {}
        status = status.loc[trade_date]['trade_status'].to_dict()
    return status


def code_classify(code):
    """判定股票所属的类别（股票/可转债）"""
    if code.startswith('1'):
        return "cb"
    elif code.startswith('0') or code.startswith('3') or code.startswith('6'):
        return 'stock'
    else:
        raise ValueError


# 给出标的代码，判断标的所属的资产大类和细分
def get_code_market(code):
    if code.startswith('688') or code.startswith('689'):  # 科创板
        return 'stock_kcb'
    elif code.startswith('6'):  # 上海主板
        return 'stock_sh'
    elif code.startswith('0'):  # 深圳主板
        return 'stock_sz'
    elif code.startswith('3'):  # 创业板
        return 'stock_cyb'
    elif code.startswith('11'):  # 上海转债
        return 'cb_sh'
    elif code.startswith('12') or code.startswith('13'):  # 深圳转债
        return 'cb_sz'


# 给定一个code_list，相应的分成上海主板、深圳主板、创业板
def code_list_market(code_list):
    if len(set([x[0] for x in code_list]) - {'0', '3', '6'}) == 0:  # 都是股票
        return dict([(x, x[0]) for x in code_list])
    elif set([x[0] for x in code_list]) == {'1'}:  # 可转债
        from DataAPI.DataToolsCbond import get_cbond_stock_map
        map_dict = get_cbond_stock_map(code_list)
        return dict([(x, map_dict[x][0]) for x in code_list])
    else:
        raise ValueError('股票和可转债混在一起，请检查')


# 获取交易的手续费
def get_cost_rate(code, type='sp'):
    if type == 'sp':
        if code_classify(code) == 'stock':
            return {'buy': 0.0000887, 'sell': 0.0010887}
        elif get_code_market(code) == 'cb_sh':
            return {'buy': 1 / 1000000, 'sell': 1 / 1000000}
        elif get_code_market(code) == 'cb_sz':
            return {'buy': 4 / 100000, 'sell': 4 / 100000}
    elif type == 'bt':
        if code_classify(code) == 'stock':
            return 0.0012
        if code_classify(code) == 'cb':
            return 0.0001


# 获取标的保单价格小数点位数
def get_price_digits(code):
    if code_classify(code) == 'stock' or get_code_market(code) == 'cb_sh':
        return 2
    elif get_code_market(code) == 'cb_sz':
        return 3


# 获取标的1手代表的股/张数
def get_min_vol_qty(code):
    if code_classify(code) == 'stock':
        return 100
    elif code_classify(code) == 'cb':
        return 10
