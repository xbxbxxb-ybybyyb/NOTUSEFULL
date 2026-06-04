from artifacts.factor_save_and_evaluate import factor_eval_save_to_dolphindb
import os
import dolphindb as ddb
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config, calc_per_factor_by_file
from AutoMiningFrame.FactorBacktest.TickFactorBacktest import FactorBacktest
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import sys
from xquant.factordata import FactorData
from collections import defaultdict
import pandas as pd



# /公共因子、标签建库建表 -- 本地 dolphindb 代码
# def create_factor_analysis_public(reCreateAnalysisTB=false, data_type='enhanced_tick'){
#   tbName = 'online_factor_analysis'

#   if (data_type == 'enhanced_tick'){
#      dbName = "dfs://PublicData/analysisdata/EnhancedTick"
# }
#    else if (data_type=='trade'){
#        dbName = "dfs://PublicData/analysisdata/Trade"
#    }
#    else if (data_type=='tick_l2p'){
#        dbName = "dfs://PublicData/analysisdata/EnhancedTickL2P"
#    }
#    else if (data_type=='tick'){
#        dbName = "dfs://PublicData/analysisdata/Tick"
#    }
#    else if (data_type=='index_enhanced'){
#        dbName = "dfs://PublicData/analysisdata/IndexEnhanced"
#    }

#   db1= database(,HASH, [SYMBOL, 10])
#   db2 = database(,HASH, [SYMBOL, 10])
#   db = database(dbName, COMPO, [db1, db2])
#   //公共库已存在，且不重新建库。可单独重建表

#   if (reCreateAnalysisTB){
#       try {dropTable(db, tbName)} catch(ex) { print ex }
#   names = ["MDDate","factor_name","label_name","stock","valid_count","skew","kurt","factor_std","label_std","normal_ic","rank_ic","auto_corr_1","auto_corr_3","auto_corr_5","corr","trade_long_return_01","trade_short_return_01","long_p_value_01","short_p_value_01","trade_long_return_02","trade_short_return_02","long_p_value_02","short_p_value_02","stratified_trade_long_return_5","stratified_trade_short_return_5","stratified_long_p_value_5","stratified_short_p_value_5","stratified_trade_long_return_10","stratified_trade_short_return_10","stratified_long_p_value_10", "tratified_short_p_value_10"]
#   types = ["DATE","STRING","STRING","STRING","LONG","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE"]
#   tbSch = table(1:0,names, types)
#   pt = db.createPartitionedTable(tbSch, tbName, `factor_name`stock)
# }}

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
    elif data_type == 'enhanced_tick':
        s.connect(host="168.17.250.48", port=8902, userid="admin", password="123456")
    return s


def calc_factor_analysis(start_date, end_date, stock, label_name, factor_list=None, data_type='enhanced_tick'):
    fp = FactorProvider('016869')
    factor_list_all = list(fp.load_info_from_dfs('factor', 'public', data_type))
    if not factor_list:
        factor_list = factor_list_all

    factor_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=factor_list, start_time=start_date,
                                                 end_time=end_date, factor_type='factor', data_type=data_type)
    factor_df_all = factor_df_all.set_index('timestamp')
    label_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=[label_name], start_time=start_date,
                                                end_time=end_date, factor_type='label', data_type=data_type)
    label_df_all = label_df_all.set_index('timestamp')

    factor_label_df = pd.merge(factor_df_all, label_df_all, left_index=True, right_index=True)
    result = factor_eval_save_to_dolphindb(factor_label_df, label=label_name, factor_list=factor_list,
                                           start_date=start_date, end_date=end_date)
    result['stock'] = stock
    return result, factor_list


def save_factor_analysis(start_date, end_date, stock, label_name, factor_list=None, data_type='enhanced_tick'):
    analysis_res, factor_name_list = calc_factor_analysis(start_date=start_date, end_date=end_date, stock=stock,
                                                          label_name=label_name, factor_list=factor_list,
                                                          data_type=data_type)
    analysis_res.to_parquet("/data/user/013150/exp_result/ALL_SYMBOL/{}/{}_all_factor_stats_df.parquet".format(data_type, stock))

    cols = ['MDDate', 'test_factor', 'label', 'stock', 'valid_count', 'skew', 'kurt', 'factor_std', 'label_std',
            'normal_ic', 'rank_ic', 'auto_corr_1', 'auto_corr_3', 'auto_corr_5', 'corr', 'trade_long_return_0.1',
            'trade_short_return_0.1', 'long_p_value_0.1', 'short_p_value_0.1', 'trade_long_return_0.2',
            'trade_short_return_0.2',
            'long_p_value_0.2', 'short_p_value_0.2', 'stratified_trade_long_return_5',
            'stratified_trade_short_return_5',
            'stratified_long_p_value_5', 'stratified_short_p_value_5',
            'stratified_trade_long_return_10', 'stratified_trade_short_return_10', 'stratified_long_p_value_10',
            'stratified_short_p_value_10']

    analysis_res = analysis_res[cols]
    analysis_res = analysis_res.rename(columns={'test_factor': 'factor_name', 'label': 'label_name'})
    analysis_res.columns = [i.replace(".", "") for i in analysis_res.columns]
    analysis_res['MDDate'] = analysis_res['MDDate'].astype(str)
    s = connect_ddb(data_type)
    if data_type == 'enhanced_tick':
        dbName = 'dfs://PublicData/analysisdata/EnhancedTick'
    elif data_type == 'tick_l2p':
        dbName = 'dfs://PublicData/analysisdata/EnhancedTickL2P'

    tbName = 'online_factor_analysis'
    s_date_dol = start_date[:4] + '.' + start_date[4:6] + '.' + start_date[6:]
    e_date_dol = end_date[:4] + '.' + end_date[4:6] + '.' + end_date[6:]
    s.upload({'analysis_res': analysis_res})
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
    start_date = '20231101'
    end_date = '20231220'
    label_list = [
        'LabelFirstPeak_th10_120s',
        # "LabelLongOneMin",
        # "LabelLongTwoMin",
        # "LabelLongFiveMin",
        # "LabelLong30Sec",
        # # "LabelShortOneMin",
        # "LabelShortTwoMin",
        # "LabelShortFiveMin",
        # "LabelShort30Sec",
    ]
    data_type = 'enhanced_tick' #'tick_l2p'
    stocks = [
        "300212.SZ",
        "002777.SZ",
        "688012.SH",
        "000034.SZ",
        "002371.SZ",
        "002409.SZ",
        "300223.SZ",
        "000977.SZ",
        "688082.SH",
        "688234.SH",
        "600702.SH",
        "300373.SZ",
        "601127.SH"
    ]
    for stock in stocks:
        for label_name in label_list:
            res = save_factor_analysis(start_date, end_date, stock, label_name, None, data_type)
            print(res)
