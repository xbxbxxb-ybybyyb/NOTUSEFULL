import pandas as pd
import numpy as np
from xquant.factordata import FactorData
from scipy.stats import rankdata
import datetime
import multiprocessing
import os 
def trans_ttm(data_df):
    data = data_df.values.T
    data_single_quarter = []
    for i in range(len(data)):
        data_single_quarter_stock = []
        for j in range(len(data[i])):
            if j % 4 !=0 :
                data_single_quarter_stock.append(data[i][j]-data[i][j-1])
            else:
                data_single_quarter_stock.append(data[i][j])
        data_single_quarter.append(data_single_quarter_stock)

    data_single_quarter_df = pd.DataFrame(data_single_quarter,columns = data_df.index, index=data_df.columns).transpose()
    data_ttm_df = data_single_quarter_df.rolling(4).sum()
    
    return data_ttm_df, data_single_quarter_df


def growthrate(data_df):
    qoq = data_df.pct_change()
    yoy = data_df.pct_change(4)
    std_3y = data_df.rolling(12).std()
    std_1y = data_df.rolling(4).std()
    
    return qoq, yoy, std_1y, std_3y
    
def ts_rank(data_df):
    tsrank4 = data_df.rolling(4).apply(lambda x: rankdata(x)[-1]/len(x))
    tsrank8 = data_df.rolling(8).apply(lambda x: rankdata(x)[-1]/len(x))
    tsrank12 = data_df.rolling(12).apply(lambda x: rankdata(x)[-1]/len(x))
    return  tsrank4, tsrank8, tsrank12


def PERFORM_SURPRISE(data_single_quarter_raw):
    def pred_ni(x):
        T = len(x)-5
        c = 0
        for i in range(T):
            c = c+x[i+4]-x[i]
        c = c/T
        return x[T]+c

    def cal_sig(x):
        T = len(x)-5

        c = 0
        for i in range(T):
            c = c+x[i+4]-x[i]
        c = c/T

        sig = 0
        for i in range(T):
            sig += np.square(x[i+4]-x[i]-c)
        return np.sqrt(sig)/(T-1)

    prediction = data_single_quarter_raw.rolling(13).apply(pred_ni)
    sigma = data_single_quarter_raw.rolling(13).apply(cal_sig)
    performace_surprise_3y = (data_single_quarter_raw-prediction)/sigma
    return performace_surprise_3y

def raw_to_normal(factor_data_df, report_apply_date):
    
    result = []
    for stock in report_apply_date.columns:
        stock_df= report_apply_date[[stock]]
        fundamental_stock = factor_data_df[[stock]]
        stock_series =stock_df.merge(fundamental_stock, left_on=stock, right_index=True, how='left')[stock+'_y']
        stock_series.name = stock
        result.append(stock_series)
    result_df = pd.DataFrame(result).transpose() 
    return result_df

def save_data(factor,factor_path,df_update):
    for indexs in df_update.index:
        num_valid_entry = np.sum(pd.notnull(df_update.loc[indexs]))
        if(num_valid_entry==0):
            print ('warning: invalid update for '+factor+' in'+str(indexs))
    
    if not os.path.exists(factor_path+factor+'.pkl'):
        print('warning: ', factor, ' not in database\n')
        df_update.to_pickle(factor_path + factor + '.pkl')
    else:
        store_data = pd.read_pickle(factor_path + factor + '.pkl')
        store_data=store_data.append(df_update)
        store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
        store_data.to_pickle(factor_path + factor + '.pkl')
def raw_to_normal_helper(factor,factor_name, report_apply_date, Fundatmental_Factor_Tmp_Path):
    
    print(factor_name)
    factor.index = pd.to_datetime(factor.index)
    factor_daily = raw_to_normal(factor, report_apply_date)
    save_data(factor_name,Fundatmental_Factor_Tmp_Path,factor_daily)
    return
    

def update_fund_factor(today,start_date='20170101'):
    num_process = 24
    Fundatmental_Factor_Tmp_Path = '/data/group/800020/AlphaDataCenter/Factor/fundamental_tmp/'
    s = FactorData()

    quarterdate = s.tradingday(start_date, today, frequency='QUARTER', dateType='ALLDAYS')[:-1]
    tradingdate = s.tradingday(start_date, today, frequency='DAY', dateType='TRADINGDAYS')[:-1]
    alldate = s.tradingday(start_date, today, frequency='DAY', dateType='ALLDAYS')[:-1]
    stock_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl').columns.tolist()
    ev_raw = s.get_factor_value('Basic_factor', stock=stock_list, mddate = tradingdate, factor_names = ['ev', ])
    mktcap_raw = s.get_factor_value('Basic_factor', stock=stock_list, mddate = alldate, factor_names = ['mkt_cap_ard', ])

    ev_mktcap_merge = ev_raw.merge(mktcap_raw,left_index=True, right_index=True, how = 'outer')
    ev_mktcap_merge = ev_mktcap_merge['ev'].unstack(level = 1).reindex(columns = stock_list)
    ev = ev_mktcap_merge.fillna(method = 'ffill')
    quarterly_ev = ev.loc[quarterdate]

    raw = s.get_factor_value('Basic_factor', stock=stock_list,mddate = quarterdate, factor_names = ['net_profit_incl_min_int_inc',
                                                                                                    'tot_shrhldr_eqy_incl_min_int',
                                                                                                    'tot_oper_rev',
                                                                                                    'tot_oper_cost',
                                                                                                    'net_cash_flows_oper_act',
                                                                                                    'free_cash_flow',
                                                                                                    'cash_cash_equ_end_period',
                                                                                                    'cash_cash_equ_beg_period', 
                                                                                                    'tot_assets', 
                                                                                                    'oper_profit',
                                                                                                    'net_profit_after_ded_nr_lp',
                                                                                                    'inventories', 
                                                                                                    'tot_cur_assets', 
                                                                                                    'acct_payable', 
                                                                                                    'tot_cur_liab', 
                                                                                                    'tot_liab' ])


    NetProfit = raw['net_profit_incl_min_int_inc'].unstack(level=1).reindex(columns = stock_list)
    Equity = raw['tot_shrhldr_eqy_incl_min_int'].unstack(level=1).reindex(columns = stock_list)
    Sales = raw['tot_oper_rev'].unstack(level=1).reindex(columns = stock_list)
    NetOprCash = raw['net_cash_flows_oper_act'].unstack(level=1).reindex(columns = stock_list)
    FCFF = raw['free_cash_flow'].unstack(level=1).reindex(columns = stock_list)
    NetCash = raw['cash_cash_equ_end_period'].unstack(level=1).reindex(columns = stock_list)-raw['cash_cash_equ_beg_period'].unstack(level=1).reindex(columns = stock_list)
    DedNetProfit = raw['net_profit_after_ded_nr_lp'].unstack(level=1).reindex(columns = stock_list)
    OprProfit = raw['oper_profit'].unstack(level=1).reindex(columns = stock_list)
    Asset = raw['tot_assets'].unstack(level=1).reindex(columns = stock_list)
    OprCost = raw['tot_oper_cost'].unstack(level=1).reindex(columns = stock_list)

    Inventory = raw['inventories'].unstack(level=1).reindex(columns = stock_list)
    AcctPayable = raw['tot_cur_assets'].unstack(level=1).reindex(columns = stock_list)
    CurAsset = raw['acct_payable'].unstack(level=1).reindex(columns = stock_list)
    Debt = raw['tot_liab'].unstack(level=1).reindex(columns = stock_list)
    CurDebt = raw['tot_cur_liab'].unstack(level=1).reindex(columns = stock_list)


    NetProfit_ttm, NetProfit_qfa = trans_ttm(NetProfit)
    Sales_ttm, Sales_qfa = trans_ttm(Sales)
    NetOprCash_ttm, NetOprCash_qfa = trans_ttm(NetOprCash)
    FCFF_ttm, FCFF_qfa = trans_ttm(FCFF)
    NetCash_ttm, NetCash_qfa = trans_ttm(NetCash)
    DedNetProfit_ttm, DedNetProfit_qfa = trans_ttm(DedNetProfit)
    OprProfit_ttm, OprProfit_qfa = trans_ttm(OprProfit)
    OprCost_ttm, OprCost_qfa = trans_ttm(OprCost)


    EP = NetProfit_ttm/ quarterly_ev
    BP = Equity.rolling(2).mean()/ quarterly_ev
    SP = Sales_ttm/ quarterly_ev
    NCFP = NetCash_ttm/ quarterly_ev
    OCFP = NetOprCash_ttm/ quarterly_ev
    FCFFP = FCFF_ttm/ quarterly_ev


    ROE_qfa = NetProfit_qfa/Equity.rolling(2).mean()
    ROA_qfa = NetProfit_qfa/Asset.rolling(2).mean()
    ROE_ttm = NetProfit_ttm/( Equity.shift(4)+Equity)/2
    ROA_ttm = NetProfit_ttm/( Asset.shift(4)+Asset)/2
    GrossProfitMargin_qfa = OprProfit_qfa/Sales_qfa
    GrossProfitMargin_ttm = OprProfit_ttm/Sales_ttm
    NetProfitMargin_qfa = NetProfit_qfa/Sales_qfa
    NetProfitMargin_ttm = NetProfit_ttm/Sales_ttm

    OprProfitToNP_qfa = OprProfit_qfa/NetProfit_qfa
    OprProfitToNP_ttm = OprProfit_ttm/NetProfit_ttm
    DedProfitToNP_qfa = DedNetProfit_qfa/NetProfit_qfa
    DedProfitToNP_ttm = DedNetProfit_ttm/NetProfit_ttm


    InventoryTurn_ttm = OprCost_ttm/( Inventory.shift(4)+Inventory)/2
    AssetTurn_ttm= Sales_ttm/( Asset.shift(4)+Asset)/2
    AccountPayableTurn_ttm = Sales_ttm/( AcctPayable.shift(4)+AcctPayable)/2
    OCFToSales_ttm = NetOprCash_ttm/Sales_ttm
    OCFToSales_qfa = NetOprCash_qfa/Sales_qfa

    DebtToAsset = Debt/Asset
    CurDebtToDebt = CurDebt/Debt


    originial = {}
    originial['EP'] = EP
    originial['BP'] = BP
    originial['SP'] = SP
    originial['NCFP'] = NCFP
    originial['OCFP'] = OCFP
    originial['FCFFP'] = FCFFP
    originial['ROE_qfa'] = ROE_qfa
    originial['ROA_qfa'] = ROA_qfa
    originial['ROE_ttm'] = ROE_ttm
    originial['ROA_ttm'] = ROA_ttm
    originial['GrossProfitMargin_qfa'] =GrossProfitMargin_qfa
    originial['GrossProfitMargin_ttm'] = GrossProfitMargin_ttm
    originial['NetProfitMargin_qfa'] = NetProfitMargin_qfa
    originial['NetProfitMargin_ttm'] = NetProfitMargin_ttm
    originial['OprProfitToNP_qfa'] = OprProfitToNP_qfa
    originial['OprProfitToNP_ttm'] = OprProfitToNP_ttm
    originial['DedProfitToNP_qfa'] = DedProfitToNP_qfa
    originial['DedProfitToNP_ttm'] = DedProfitToNP_ttm
    originial['InventoryTurn_ttm'] = InventoryTurn_ttm
    originial['AssetTurn_ttm'] = AssetTurn_ttm
    originial['AccountPayableTurn_ttm'] = AccountPayableTurn_ttm
    originial['OCFToSales_ttm'] = OCFToSales_ttm
    originial['OCFToSales_qfa'] = OCFToSales_qfa
    originial['DebtToAsset'] = DebtToAsset
    originial['CurDebtToDebt'] = CurDebtToDebt

    all_ttm = ['ROE_ttm','ROA_ttm','GrossProfitMargin_ttm','NetProfitMargin_ttm','OprProfitToNP_ttm','DedProfitToNP_ttm','InventoryTurn_ttm','AccountPayableTurn_ttm','OCFToSales_ttm','AssetTurn_ttm','DebtToAsset','CurDebtToDebt',]
    all_factor = sorted(list(originial.keys()))

    all_quarter = ['ROE_qfa', 'ROA_qfa','GrossProfitMargin_qfa', 'OprProfitToNP_qfa','NetProfitMargin_qfa', 'DedProfitToNP_qfa','OCFToSales_qfa']

    New_Factors= {}
    
    for factor in all_factor:
        tsrank4, tsrank8, tsrank12 = ts_rank(originial[factor])
        New_Factors[factor+'_tsrank4'] = tsrank4
        New_Factors[factor+'_tsrank8'] = tsrank8
        New_Factors[factor+'_tsrank12'] = tsrank12

    for factor in all_ttm:
        qoq, yoy, std_1y, std_3y = growthrate(originial[factor])
        New_Factors[factor+'_qoq'] = qoq
        New_Factors[factor+'_yoy'] = yoy
        New_Factors[factor+'_std_1y'] = std_1y
        New_Factors[factor+'_std_3y'] = std_3y

    for factor in all_quarter:
        surprise  = PERFORM_SURPRISE(originial[factor])
        New_Factors[factor+'_surprise'] = surprise
    
    surprise  = PERFORM_SURPRISE(NetProfit_qfa)
    New_Factors['NetProfit_surprise'] = surprise

    surprise  = PERFORM_SURPRISE(Sales_qfa)
    New_Factors['Sales_surprise'] = surprise

    surprise  = PERFORM_SURPRISE(NetOprCash_qfa)
    New_Factors['NetOprCash_surprise'] = surprise

    surprise  = PERFORM_SURPRISE(FCFF_qfa)
    New_Factors['FCFF_surprise'] = surprise

    surprise  = PERFORM_SURPRISE(NetCash_qfa)
    New_Factors['NetCash_surprise'] = surprise

    surprise  = PERFORM_SURPRISE(DedNetProfit_qfa)
    New_Factors['DedNetProfit_surprise'] = surprise

    surprise  = PERFORM_SURPRISE(OprProfit_qfa)
    New_Factors['OprProfit_surprise'] = surprise
    
    surprise  = PERFORM_SURPRISE(OprCost_qfa)
    New_Factors['OprCost_surprise'] = surprise


 
    report_apply_date = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/report_apply_date.pkl')['20150101':]
    report_apply_date = report_apply_date.apply(pd.to_datetime,format = '%Y%m%d') 



    pool = multiprocessing.Pool(processes=num_process)
    manager = multiprocessing.Manager()

    Process = []
    for factor in New_Factors.keys():
        Process.append(pool.apply_async(raw_to_normal_helper, args=(New_Factors[factor], 
                                                            factor,
                                                            report_apply_date, 
                                                            Fundatmental_Factor_Tmp_Path)))
                                
    for i, elem in enumerate(Process):
        elem.get()
    pool.close()
    pool.join()
today = datetime.datetime.now().strftime('%Y%m%d')
update_fund_factor(today,20100101)

