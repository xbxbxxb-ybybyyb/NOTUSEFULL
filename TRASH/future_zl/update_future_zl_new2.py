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
    month, day = int(date[-4:-2]), int(date[-2:])
    if contract_id.split('.')[1] == 'ZCE':
        contract_month =  int(contract_id.split(".")[0][-2:])
    else:
        contract_month = int(contract_id.split(".")[0][-2:])
    xq_logger.info("contract_id:{}, contract_month:{}, month:{}, day:{}".format(contract_id, contract_month, month, day))
    if contract_month-month <= 1 and day>=25:
        return True
    return False

def __is_change_future(old_contract_id, first_contract_id):
    if not old_contract_id == True:
        return True
    #判断合约时间先后顺序
    if old_contract_id.split(".")[1] == "ZCE":
        new_code_number = first_contract_id[len(symbol):len(symbol) + __code_len(first_contract_id)]
        old_code_number = old_contract_id[len(symbol):len(symbol) + __code_len(old_contract_id)]
        # ZCE中，第一位为年份位数，后两位为月份。
        if new_code_number[0] == '0':
            new_code_number = "2"+new_code_number
            if old_code_number[0] == '0':
                old_code_number = "2"+new_code_number
            else:
                old_code_number = "1" + new_code_number
    else:
        new_code_number = first_contract_id[len(symbol):len(symbol) + __code_len(first_contract_id)]
        old_code_number = old_contract_id[len(symbol):len(symbol) + __code_len(old_contract_id)]
    if new_code_number>old_code_number:
        #成交量最大合约到期日晚于旧合约
        return True
    else:
        return False


def get_pre_zlcode(new_zl00_id, symbol, contract_type, old_contract_ids, old_contract_dates):
    """
    从前一天开始遍历上一份主力合约id，如果和今日的主力合约相同，继续往前追溯，直到找到和今日主力合约ID不同的上一份主力合约ID。
    :param new_zl00_id: 今日主力合约ID
    :param old_contract_ids: 从前一天开始的所有历史主力合约列表
    :param old_contract_dates:
    :return:
    """
    if len(old_contract_ids) == 0:
        #上一份主力合约不存在，可能是历史上还未有行情
        xq_logger.warning("未取到前一个主力合约(second){} {}。".format(date, new_zl00_id))
        return pd.DataFrame()

    pre_zl_contract_id = -1
    if new_zl00_id == None:
        pre_zl_contract_id = 0#最近一天的主力合约ID
    else:
        for id_idx in range(len(old_contract_ids)):
            if old_contract_ids[len(old_contract_ids)-1-id_idx] == new_zl00_id:
                continue
            else:
                pre_zl_contract_id = id_idx
                break
    if pre_zl_contract_id == -1:
        #和今日主力合约ID不同的上一份主力合约ID未找到
        xq_logger.warning("未找到和今日主力合约ID：{} 不同的上一份主力合约ID{}。".format(new_zl00_id, date))
        return pd.DataFrame()
    else:
        pre_zl_date = old_contract_dates[len(old_contract_ids) - 1 - pre_zl_contract_id]
        startdate = df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (
                df_zl["TDATE"] == pre_zl_date)].iloc[0]["ZL_STARTDATE"]
        pre_zl_value = df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (
                df_zl["TDATE"] == startdate)].iloc[0]
    # print(pre_zl_value)
    return pre_zl_value


fa = FactorData()
fd = FutureData()
ma = MarketData()

symbol = "CF"
date = "20201014"
contract_type = "ZL00"
future_type="Commodity"  #'Financial' #"Commodity":
dates = fa.tradingday("20190211", "20191030")
df_zl = get_contract_zl_info(symbol, contract_type, dates[0])  # 获取主力合约信息

for date in dates:
    print("="*100)
    change_store0 = False
    old_contract_ids = df_zl["ZL_MAPPINGCODE"].tolist()
    old_contract_dates = df_zl["TDATE"].tolist()
    old_contract_startdate = df_zl["ZL_STARTDATE"].tolist()

    symbol_code = fd.get_instrument_all(symbol, fa.tradingday(date, -30)[0], int(date))#查询当日可交易的标的
    xq_logger.info("当日可交易的标的为：{}:".format(symbol_code))
    df_value = pd.DataFrame()
    for code in symbol_code:
        df_1 = ma.getMDSecurityKLineDataFrame(code, "{}000000000".format(date), "{}000000000".format(date), 10, 25)
        if not df_1.empty:
            df_value = pd.concat([df_value, df_1])#全部合约数据

    new_zl00_id = None
    new_zl00_date = date

    if df_value.empty:
        xq_logger.error("该品种今日无主力数据：symbol:{0},date:{1}".format(symbol, date))
    else:
        df_value = df_value[['HTSCSecurityID', 'TotalVolumeTrade', 'TotalValueTrade', 'ClosePx']]
        df_value.set_index('HTSCSecurityID', inplace=True)
        df_value = df_value.sort_values(by='TotalVolumeTrade', ascending=False)
        if contract_type == "ZL01":
            df_value = df_value.drop(index = df_value.index[0])
        if df_value.empty:
            xq_logger.error("该品种今日无次主力数据：symbol:{0},date:{1}".format(symbol, date))
        else:
            xq_logger.info("df_value: {}".format(df_value))

            contract_f_c = df_value.index.values.tolist()  #按成交量排序
            xq_logger.info("成交量从大到小次排序：{}".format(contract_f_c))

            old_contract_id = old_contract_ids[-1]#前一日主力合约的真实合约
            try:
                old_rank = contract_f_c.index(old_contract_id)
            except ValueError:
                xq_logger.warning("上一日的zl contract_id 已经退市, 没有取到相关行情:{}, {}".format(old_contract_id, date))
                old_rank = 1000#没有行情，排名最后

            if old_rank!=0:
                first_contract = contract_f_c[0]  # 成交量最大的合约
                xq_logger.info("Date:{}, 成交量最大合约改变，从{}变为{}。".format(date, old_contract_id, first_contract))
                #前一日主力合约非今日成交量最大合约
                for i in range(0, min(old_rank,len(contract_f_c))):
                    print(contract_f_c, old_contract_ids, first_contract[len(symbol):len(symbol) + __code_len(first_contract)])
                    first_contract = contract_f_c[i]#今日主力合约候选
                    xq_logger.info("new_zl_code: {}, old_zl_code: {}。".format(first_contract, old_contract_id))
                    if __is_change_future(old_contract_id, first_contract):
                        xq_logger.info("prepare change ZL00 code, from {} to {}:".format(old_contract_id, first_contract))
                        change_store0 = True
                        new_zl00_id = first_contract
                        break
                if change_store0 == False:
                    xq_logger.info("Date {}: Although volumn is not max, stay unchange ZL00 code， from {} to {}, then judge force change:".format(date, old_contract_id, first_contract))
            if change_store0 == False:
                if future_type == 'Financial':
                    new_zl00_id = old_contract_id
                    if old_rank == 0:
                        xq_logger.info("{} 前一日主力合约，仍是今日成交量最大合约，判断结束。{}:{}".format(future_type, new_zl00_id, date))
                    else:
                        xq_logger.info("{} 前一日主力合约，非今日成交量最大合约，但成交量更大合约不满足换仓条件，判断结束。{}:{}".format(future_type, new_zl00_id, date))
                elif future_type == "Commodity":
                    new_zl00_id = old_contract_id
                    if not __is_change_month_date(new_zl00_id , date):
                        # 不需强制换仓
                        if old_rank == 0:
                            xq_logger.info("{} 前一日主力合约，仍是今日成交量最大合约，且非进入交割月前一月25号强制换仓，判断结束。{}:{}".format(future_type, new_zl00_id, date))
                        else:
                            xq_logger.info(
                                "{} 前一日主力合约，非今日成交量最大合约，但成交量更大合约不满足换仓条件，且非进入交割月前一月25号强制换仓，判断结束。{}:{}".format(future_type, new_zl00_id, date))
                    else:
                        #商品期货，如果下个月是交割月，且本月日期大于25号，需要换仓。
                        for alter_code in contract_f_c[1:]:
                            if __is_change_future(old_contract_id, first_contract):
                                xq_logger.info(
                                    "prepare change ZL00 code, from {} to {}:".format(old_contract_id, first_contract))
                                change_store0 = True
                                new_zl00_id = first_contract
                            else:
                                xq_logger.info(
                                    "failed change ZL00 code, from {} to {}:".format(old_contract_id, first_contract))
                        if change_store0 == False:
                            # 应该不会出现这种情况:
                            new_zl00_id = old_contract_id
                            xq_logger.warning("满足强制换仓条件，但无可选合约供换仓 from {} to {}".format(old_contract_id, "None"))


    #判断历史上前一份主力合约是否存在,为了获取上一份合约的价格
    pre_zl_value = get_pre_zlcode(new_zl00_id, symbol, contract_type, old_contract_ids, old_contract_dates)#获取前一个主力合约的换仓日

    #判断历史上上一份和今日zl合约不同的主力合约
    if pre_zl_value.empty:
        has_pre_zl = False
    else:
        has_pre_zl = True

    if new_zl00_id != None:
        #今日有行情
        cur_close, adj, total_volume = df_value.loc[new_zl00_id, "ClosePx"], np.nan, df_value.loc[new_zl00_id, "TotalVolumeTrade"]
        mappingcode = new_zl00_id
    else:
        # 可能是无行情
        xq_logger.warning("这一日的zl contract_id 已经退市, 没有取到相关行情:{}, {}".format(new_zl00_id, date))
        cur_close, adj, total_volume = np.nan, np.nan, np.nan
        mappingcode = pre_zl_value["ZL_MAPPINGCODE"]

    if has_pre_zl:
        startdate, last_close = pre_zl_value["ZL_STARTDATE"], pre_zl_value["ZL_CUR_CLOSE"]
        adj =  adj
    else:
        startdate, last_close, adj = np.nan, np.nan, np.nan

    if change_store0:
        mappingcode = new_zl00_id
        startdate = date

    tmp_list = [symbol, date, symbol + contract_type, mappingcode, startdate, last_close, cur_close, adj, total_volume ]

    if not df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (df_zl["TDATE"] ==date)].empty:
        #更新模式
        df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol + contract_type) & (df_zl["TDATE"] ==date)] = tmp_list
        xq_logger.info("update df_zl: {}".format(tmp_list))
    else:
        #追加模式
        df_zl =  df_zl.append(pd.DataFrame([tmp_list],columns=df_zl.columns), ignore_index=True)
        xq_logger.info("append df_zl: {}".format(tmp_list))
    print(df_zl[(df_zl["CODE"] == symbol) & (df_zl["ZL_CODE"] == symbol+contract_type) & (df_zl["TDATE"]<=date) & (fa.tradingday(date, -10)[0]<df_zl["TDATE"])][["TDATE", 'ZL_MAPPINGCODE', 'ZL_STARTDATE','ZL_LAST_CLOSE', 'ZL_CUR_CLOSE']])


df_zl.to_csv("df_zl.csvs")
