from MDCDataProvider.futuredata.future import DataProvider2
import pandas as pd
from xquant.thirdpartydata.marketdata import MarketData
from xquant.futuredata import FutureData
from xquant.factordata import FactorData
from xquant import xq_logger
import numpy as np

def get_contract_zl_info(symbol, contract_type, date):
    """
    获取主力合约信息
    :param symbol:
    :param contract_type:
    :param date:
    :return:
    """
    fddp = DataProvider2()
    df_zl = fddp.get_contract_data("CONTRACT_ZL_INFO.parquet", 'ZL_INFO')
    df_zl = df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (df_zl["TDATE"] < date)]
    return df_zl


CF_CONTRACT_LIST = ['IF', 'IC', 'IH']
SHF_CONTRACT_LIST = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'SC', 'FU', 'BU',
                          'RU', 'SP']
ZCE_CONTRACT_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP',
                          'TA', 'FG', 'SF', 'MA', 'ZC', 'SM']
DCE_CONTRACT_LIST = ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD',
                          'L', 'V', 'PP', 'J', 'JM', 'I', 'EG']
def __code_len(symbol):
    if symbol in ZCE_CONTRACT_LIST:
        code_len = 3
    else:
        code_len = 4
    return code_len

def __is_change_month_date(contract_id, date):
    #针对商品期货，判断是否晚于交割月前一月且是25日之后的强制换仓日
    month, day = int(date[-4,:-2]), int(date[-2:])
    if contract_id.split('.')[1] == 'ZCE':
        contract_month =  int(contract_id.split(".")[0][-2:])
    xq_logger.info("contract_id:{}, contract_month:{}, month:{}, day:{}".format(contract_id, contract_month, month, day))
    if contract_month-month <= 1 and day>=25:
        return True
    return False


def get_pre_zlcode(old_contract_ids, old_contract_dates):
    #查找上一个主力合约及对应日期(倒序查找)
    first_pre_id = old_contract_ids[-1]
    first_pre_date = old_contract_dates[-1]

    for id_idx in range(len(old_contract_ids)):
        if old_contract_ids[len(old_contract_ids)-1-id_idx] == first_pre_id:
            continue
        else:
            second_pre_id = old_contract_ids[len(old_contract_ids)-1-id_idx]
            second_pre_date = old_contract_dates[len(old_contract_ids)-1-id_idx]
            break
    return (first_pre_id, first_pre_date), (second_pre_id,second_pre_date)




fa = FactorData()
fd = FutureData()
ma = MarketData()

symbol = "IH"
date = "20201014"
contract_type = "ZL00"
future_type='Financial'

for date in fa.tradingday("20201015", "20201105"):
    print("="*100)
    change_store0 = False
    df_zl = get_contract_zl_info(symbol, contract_type, date)#获取主力合约信息

    old_contract_ids = df_zl["ZL_MAPPINGCODE"].tolist()
    old_contract_dates = df_zl["TDATE"].tolist()
    old_contract_startdate = df_zl["ZL_STARTDATE"].tolist()

    new_zl00_id = None

    symbol_code = fd.get_instrument_all(symbol, int(date), int(date))#查询当日可交易的标的
    xq_logger.info("当日可交易的标的为：{}:".format(symbol_code))
    df_value = pd.DataFrame()
    for code in symbol_code:
        df_1 = ma.getMDSecurityKLineDataFrame(code, "{}000000000".format(date), "{}000000000".format(date), 10, 25)
        if not df_1.empty:
            df_value = pd.concat([df_value, df_1])#全部合约数据

    if df_value.empty:
        xq_logger.error("该品种今日无数据：symbol:{0},date:{1}".format(symbol, date))

    df_value = df_value[['HTSCSecurityID', 'TotalVolumeTrade', 'TotalValueTrade', 'ClosePx']]
    df_value.set_index('HTSCSecurityID', inplace=True)
    df_value = df_value.sort_values(by='TotalVolumeTrade', ascending=False)
    xq_logger.info("df_value: {}".format(df_value))

    contract_f_c = df_value.index.values.tolist()  #按成交量排序
    xq_logger.info("成交量从大到小次排序：{}".format(contract_f_c))

    try:
        first_contract = contract_f_c[0]  # 成交量最大的合约
        if first_contract == old_contract_ids[-1]:
            xq_logger.info("Date: {}, 成交量最大合约保持不变，为{}，{}".format(date, first_contract, old_contract_ids[-1]))
        else:
            xq_logger.info("Date:{}, 成交量最大合约改变，从{}变为{}。".format(date, first_contract, old_contract_ids[-1]))
    except:
        xq_logger.warning("该品种今日无数据：symbol:{0},date:{1}".format(symbol, date))
        raise Exception()

    old_contract_id = old_contract_ids[-1]#前一日主力合约的真实合约
    try:
        old_rank = contract_f_c.index(old_contract_id)
    except ValueError:
        xq_logger.warning("上一日的zl contract_id 已经退市, 没有取到相关行情:{}, {}".format(old_contract_id, date))
        old_rank = 1000#没有行情，排名最后
    new_zl00_date = date

    if old_rank!=0:
        #前一日主力合约非今日成交量最大合约
        for i in range(0, old_rank):
            first_contract = contract_f_c[i]#今日主力合约候选
            new_code_number = first_contract[len(symbol):len(symbol) + __code_len(first_contract)]
            old_code_number = old_contract_id[len(symbol):len(symbol) + __code_len(old_contract_id)]
            xq_logger.info("new_code_number: {}, old_code numer: {}。".format(new_code_number, old_code_number))
            if new_code_number > old_code_number:
                xq_logger.info("prepare change ZL00 code, from {} to {}:".format(old_contract_id, first_contract))
                change_store0 = True
                new_zl00_id = first_contract
                break
        if change_store0 == False:
            xq_logger.info("Date {}: Although volumn is not max, stay unchange ZL00 code, from {} to {}:".format(date, old_contract_id, first_contract))
    else:
        new_zl00_id = old_contract_id
        if future_type == 'Financial':
            xq_logger.info("{} 前一日主力合约，仍是今日成交量最大合约，判断结束。{}:{}".format(future_type, new_zl00_id, date))
        elif future_type == "Commodity":
            if not __is_change_month_date(new_zl00_id , date):
                # 不需强制换仓
                new_zl00_id = old_contract_id
                xq_logger.info("{} 前一日主力合约，仍是今日成交量最大合约，且非交割月，判断是否强制换仓。{}:{}".format(future_type, symbol, date))
            else:
                #商品期货，如果下个月是交割月，且本月日期大于25号，需要换仓。
                for alter_code in contract_f_c[1:]:
                    new_code_number = alter_code[len(alter_code):len(alter_code) + __code_len(alter_code)]
                    old_code_number = old_contract_id[
                                      len(old_contract_id):len(old_contract_id) + __code_len(old_contract_id)]
                    if new_code_number > old_code_number:
                        xq_logger.info(
                            "prepare change ZL00 code, from {} to {}:".format(old_code_number, first_contract))
                        change_store0 = True
                        new_zl00_id = first_contract
                        new_zl00_date = date
                    else:
                        xq_logger.info(
                            "failed change ZL00 code, from {} to {}:".format(old_code_number, first_contract))
                if change_store0 == False:
                    # 应该不会出现这种情况:
                    pass

    first_pre_zl_pair, second_pre_zl_pair = get_pre_zlcode(old_contract_ids, old_contract_dates)
    if new_zl00_id == first_pre_zl_pair[0]:
        pre_zl_value = df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (
                    df_zl["TDATE"] == second_pre_zl_pair[1])].iloc[0]
    else:
        #['CODE', 'TDATE', 'ZL_CODE', 'ZL_MAPPINGCODE', 'ZL_STARTDATE','ZL_LAST_CLOSE', 'ZL_CUR_CLOSE', 'ZL_ADJ', 'ZL_TOTAL_VOLUMETRADE']
        pre_zl_value = df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (
                    df_zl["TDATE"]== first_pre_zl_pair[1])].iloc[0]
    xq_logger.info("当日{}主力合约为{}， 前移仓合约是pre_zl_value: {}".format(date,new_zl00_id, pre_zl_value["ZL_MAPPINGCODE"]))

    mappingcode, startdate, last_close = \
        old_contract_ids[-1], old_contract_startdate[-1], np.nan
    cur_close, adj, total_volume = df_value.loc[new_zl00_id, "ClosePx"], np.nan, df_value.loc[new_zl00_id, "TotalVolumeTrade"]

    if change_store0:
        mappingcode = new_zl00_id
        startdate = date
        last_close = pre_zl_value["ZL_CUR_CLOSE"]
        adj =  cur_close - last_close

    tmp_list = [symbol, date, symbol + contract_type, mappingcode, startdate, last_close, cur_close, adj, total_volume ]

    if not df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (df_zl["TDATE"] ==date)].empty:
        #更新模式
        df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (df_zl["TDATE"] ==date)] = tmp_list
        xq_logger.info("update df_zl: {}".format(tmp_list))
    else:
        #追加模式
        df_zl.loc[len(df_zl)] = tmp_list
        xq_logger.info("append df_zl: {}".format(tmp_list))
    print(df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol+contract_type) & (df_zl["TDATE"]<=date) & (fa.tradingday(date, -10)[0]<df_zl["TDATE"])][["TDATE", 'ZL_MAPPINGCODE', 'ZL_STARTDATE','ZL_LAST_CLOSE', 'ZL_CUR_CLOSE']])




# if future_type == "Commodity" and __is_change_date(date,  'next'):
#     contract_all = df_value.sort_values(by='TotalValueTrade', ascending=False).index.values
#     if contract_24 and contract_24[-1] == contract_all[0]:
#         df_value.drop(index=[contract_all[0]], inplace=True)
