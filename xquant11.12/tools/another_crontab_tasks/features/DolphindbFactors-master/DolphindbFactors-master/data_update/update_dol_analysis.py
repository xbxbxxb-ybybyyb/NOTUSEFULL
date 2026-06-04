from artifacts.factor_save_and_evaluate import factor_eval_save_to_dolphindb 
import os
import numpy as np
import pandas as pd
import dolphindb as ddb
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.FactorBacktest.TickFactorBacktest import FactorBacktest
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import sys
fp = FactorProvider('016869')
fb = FactorBacktest()
fd = FactorData()

def get_env():
    # 判断运行程序的系统
    if os.environ.get("ENV_VERSION"):
        sysFlag = "xquant"
    elif os.environ.get("DSWMAP_envTag"):
        sysFlag = "tquant"
    elif os.environ.get('BIG_DATA_PREPATH', False) and not os.environ.get('ENV_VERSION', False):
        sysFlag = "big_data"
    else:
        sysFlag = "outside"
        os.environ['outside_env'] = 'uat'

    # 判断系统的运行环境是生产还是测试
    if sysFlag == "xquant":
        envFlag = os.environ.get("ENV_VERSION")
    elif sysFlag == "tquant":
        envFlag = os.environ.get("DSWMAP_envTag")
    elif sysFlag == "outside":
        envFlag = os.environ.get("outside_env")

    if envFlag.lower() == "prd":
        env = "prd"
    elif envFlag.lower() == "uat":
        env = "uat"
    else:
        raise Exception('当前只有prd/uat环境有数据')
    return env


def connect_ddb(data_type):
    s = ddb.session()
    if data_type == 'tick_l2p':
        s.connect(host="168.17.249.172", port=8902, userid="admin", password="123456")
    elif data_type in ['enhanced_tick','enhanced_tick_norm']:
        s.connect(host="168.17.250.48", port=8902, userid="admin", password="123456")
    return s

def get_stocks_list(data_type):
    s = connect_ddb(data_type)
    if data_type in ['enhanced_tick','enhanced_tick_norm']:
        dbName = 'dfs://PublicData/platformdata/EnhancedTick'
        if data_type == 'enhanced_tick':
            tbName = 'online_factor_data'
        else:
            tbName = 'online_factor_data_new'

    elif data_type == 'tick_l2p':
        dbName = 'dfs://PublicData/platformdata/EnhancedTickL2P'
        tbName = 'online_factor_data'
    stocks = s.run(f"""
    dbname = "{dbName}"
    tbname = `{tbName}
    pt = loadTable(dbname, tbname)
    stocks = exec distinct(M_HTSCSecurityID) from pt
    stocks
    """)
    return list(stocks)
               

def calc_factor_analysis(start_date, end_date, stock, label_name, factor_list=None, data_type='enhanced_tick'):
    factor_list_all = list(fp.load_info_from_dfs('factor','public',data_type))
    if not factor_list:
        factor_list = factor_list_all
        
    factor_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=factor_list, start_time=start_date,end_time=end_date, factor_type='factor', data_type=data_type)
    factor_df_all = factor_df_all.set_index('timestamp')
    label_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=[label_name], start_time=start_date,end_time=end_date, factor_type='label', data_type=data_type)
    label_df_all = label_df_all.set_index('timestamp')
    
    factor_label_df = pd.merge(factor_df_all, label_df_all, left_index=True, right_index=True)
    result = factor_eval_save_to_dolphindb(factor_label_df,  label = label_name, factor_list = factor_list, start_date = start_date, end_date = end_date)
    result['stock'] = stock
    return result, factor_list
    

def save_factor_analysis(start_date, end_date, stock, label_name, factor_list=None, data_type='enhanced_tick'):
    analysis_res, factor_name_list = calc_factor_analysis(start_date=start_date, end_date=end_date, stock=stock, label_name=label_name, factor_list=factor_list, data_type=data_type)
    cols = ['MDDate', 'test_factor', 'label', 'stock', 'valid_count', 'skew', 'kurt', 'factor_std', 'label_std', 
            'normal_ic', 'rank_ic', 'auto_corr_1', 'auto_corr_3', 'auto_corr_5', 'corr', 'trade_long_return_0.1', 
            'trade_short_return_0.1', 'long_p_value_0.1', 'short_p_value_0.1', 'trade_long_return_0.2', 'trade_short_return_0.2', 
            'long_p_value_0.2', 'short_p_value_0.2', 'stratified_trade_long_return_5', 'stratified_trade_short_return_5', 
            'stratified_long_p_value_5', 'stratified_short_p_value_5', 
            'stratified_trade_long_return_10', 'stratified_trade_short_return_10', 'stratified_long_p_value_10', 
            'stratified_short_p_value_10']
    
    analysis_res = analysis_res[cols]
    analysis_res = analysis_res.rename(columns={'test_factor':'factor_name','label':'label_name'})
    analysis_res.columns = [i.replace(".","") for i in analysis_res.columns] 
    analysis_res['MDDate'] = analysis_res['MDDate'].astype(str)
    s = connect_ddb(data_type)
    if data_type in ['enhanced_tick','enhanced_tick_norm']:
        dbName = 'dfs://PublicData/analysisdata/EnhancedTick'
        if data_type == 'enhanced_tick':
            tbName = 'online_factor_analysis'
        else:
            tbName = 'online_norm_factor_analysis'

    elif data_type == 'tick_l2p':
        dbName = 'dfs://PublicData/analysisdata/EnhancedTickL2P'
        tbName = 'online_factor_analysis'

    
    s_date_dol = start_date[:4] + '.' + start_date[4:6] + '.' + start_date[6:]
    e_date_dol = end_date[:4] + '.' + end_date[4:6] + '.' + end_date[6:]
    s.upload({'analysis_res':analysis_res})
    # 判断是否已有数据
    script_check_data = f'''
    select count(*) from loadTable("{dbName}",`{tbName}) where MDDate in {s_date_dol}..{e_date_dol},stock=='{stock}',label_name=='{label_name}',factor_name in {factor_name_list}
    
    '''
    print(script_check_data)
    cnt = s.run(script_check_data)
    
    if cnt.iloc[0, 0] > 0:
        print("先删除")
        script_delete = f'''
        delete from loadTable("{dbName}",`{tbName}) where MDDate in {s_date_dol}..{e_date_dol},stock=='{stock}',label_name=='{label_name}',factor_name in {factor_name_list}
        '''
        s.run(script_delete)
    print(analysis_res)
    save_data = f"""
        dbName = "{dbName}"
        tbName = `{tbName}
        tb = loadTable(dbName, tbName)
        analysis_res.replaceColumn!(`MDDate, temporalParse(analysis_res.MDDate, `yyyyMMdd))
        tb.append!(analysis_res)
    """
    s.run(save_data)
    return
    
if __name__ == "__main__":
    import datetime
    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    # 标签名
    label_name_list = ['LabelFirstPeak_th10_120s','LabelFirstPeak_th05_120s']
    # 研究场景
    data_type = 'enhanced_tick_norm' # 'enhanced_tick'
    # 标的列表
    stock_list = ['510300.SH','510500.SH']
    #stock_list = get_stocks_list(data_type)
     
    # 起止时间
    s_date = sorted([str(y)+'0101' for y in range(2020,2024)]+[str(y)+'0701' for y in range(2020,2024)])
    e_date = sorted([str(y)+'0630' for y in range(2020,2024)]+[str(y)+'1231' for y in range(2020,2024)])
    date_list = sorted(set(zip(s_date, e_date)))
    
    # 启动补数    
    for stock in stock_list:
        for start_date, end_date in date_list:
            for label_name in label_name_list:    
                try:
                    print(stock, stock_list.index(stock)/len(stock_list), start_date, end_date)
                    res = save_factor_analysis(start_date, end_date, stock, label_name, None, data_type)
                    print(res)
                except:
                    continue

