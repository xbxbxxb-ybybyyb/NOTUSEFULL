from tquant.conf.DubboConf import get_jurisdictionData

jurisdictionData_dict = {}


def __set_jurisdictionData():
    c_name = "jurisdictionData"
    global jurisdictionData_dict
    if not jurisdictionData_dict.get(c_name):
        jurisdictionData_dict[c_name] = get_jurisdictionData()


def get_factors_info():
    __set_jurisdictionData()
    data = jurisdictionData_dict["jurisdictionData"]
    Basic_factordata = data["因子信息"]["jurisdictionData"]["Basic_factordata"]
    cata_name_dict = {'行情指标': 'market', '估值指标': 'valuation', '财务分析': 'financialanalysis',
                      '财务报表': 'financialreport', '风险分析': 'riskanalysis'}
    # 元数据目录id有新增或变动时需更改
    catalog_id_dict = {2: 'market', 3: 'valuation', 4: 'financialreport', 5: 'dividendindex', 6: 'newmsgindex',
                       7: 'conforecastindex', 8: 'financialanalysis', 9: 'riskanalysis', 10: 'alpha',
                       11: 'barra', 12: 'technicalanalysis', 13: 'momentum', 14: 'emotion'}
    factorInfo = Basic_factordata["factorInfo"]
    factors_info = {}
    for f in factorInfo:
        catalog_name = catalog_id_dict.get(factorInfo[f]["idInfo"][-2])
        if not catalog_name:
            continue
        if not factors_info.get(catalog_name):
            factors_info[catalog_name] = [f]
        else:
            factors_info[catalog_name].append(f)
    return factors_info


def get_factor_table(factor_list):
    __set_jurisdictionData()
    data = jurisdictionData_dict["jurisdictionData"]
    Basic_factordata = data["因子信息"]["jurisdictionData"]["Basic_factordata"]
    factorInfo = Basic_factordata["factorInfo"]
    f_table = {}
    for f in factorInfo.keys():
        if f in factor_list:
            if not f_table.get(factorInfo[f]['table']):
                f_table[factorInfo[f]['table']] = [f]
            else:
                f_table[factorInfo[f]['table']].append(f)
    return f_table
