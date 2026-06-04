import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, '/data/group/800020/AlphaTools/')
from optimize import optimize_hf as opthf
from BacktestHF import BacktestHF as bthf
def save_data(path,df_update):
    if os.path.exists(path):
        store_data = pd.read_pickle(path )
        store_data=store_data.append(df_update)
        store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
    else:
        store_data = df_update
    store_data.to_pickle(path)
    return store_data
hedge_index = 'ZZ500'
capital = 20.e7
barra_limit_dict = {
    'Beta'+hedge_index[-3:]: (0.01, 0.01), 
    'Momentum':              (0.01, 0.01), 
    'Size':                  (1000, 1000), 
        'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
industry_loose = 0.001
amt_limit = 0.1
benchmark = '500'
open_position_pm = False
sim_w_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/weight_bk/20200601/'
real_w_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/'
predict_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/'
simulation_w_am_path = sim_w_path + 'simulation_w_am.pkl'
simulation_w_pm_path = sim_w_path + 'simulation_w_pm.pkl'
simulation_w_vwap_path = sim_w_path + 'simulation_w_vwap.pkl'
real_w_am_path = real_w_path + 'real_w_am.pkl'
real_w_pm_path = real_w_path + 'real_w_pm.pkl'
real_w_vwap_path = real_w_path + 'real_w_vwap.pkl'
real_w_am = pd.read_pickle(real_w_am_path)
real_w_pm = pd.read_pickle(real_w_pm_path)
real_w_vwap = pd.read_pickle(real_w_vwap_path)
a_am_path = predict_path+'am/All_'+benchmark+'/'
a_pm_path = predict_path+'pm/All_'+benchmark+'/'
a_vwap_path = predict_path+'vwap/All_'+benchmark+'/'

last_date = sorted(os.listdir(a_am_path))[-2][:-4]
today_date = sorted(os.listdir(a_am_path))[-1][:-4]
print(last_date, today_date)
benchmark = '300'
open_position_pm = False
sim_w_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/'
real_w_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/'
predict_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/'
simulation_w_vwap300_path = sim_w_path + 'simulation_w_vwap.pkl'
real_w_vwap300_path = real_w_path + 'real_w_vwap.pkl'
real_w_vwap300 = pd.read_pickle(real_w_vwap300_path)
a_vwap300_path = predict_path+'vwap/All_'+benchmark+'/'
hf_w_start_date = '20200601'
vwap_w_start_date = '20200511'
vwap300_w_start_date = '20200101'
open_date = '20200515'
shipan_track={}
w_am0 = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/weight_bk/20200515/simulation_w_am.pkl')
w_pm0 = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/weight_bk/20200515/simulation_w_pm.pkl')
w_vwap0 = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/weight_bk/vwap_5e8.pkl')
w_am = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_500/simulation_w_am.pkl').loc[hf_w_start_date:today_date]
w_pm = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_500/simulation_w_pm.pkl').loc[hf_w_start_date:today_date]
w_vwap = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_500/simulation_w_vwap.pkl').loc[vwap_w_start_date:today_date]
w_vwap300 = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_300/simulation_w_vwap.pkl').loc[vwap300_w_start_date:today_date]
def get_open_position_w(open_o32_date,pf_code):
    
    x = pd.read_excel(o32_path + '综合信息查询_组合证券_' + open_o32_date + '.xls', converters={'组合名称':str, '证券代码':str})
    x = x[(x['组合名称']==pf_code) & (x['证券类别']=='股票')]
    x.index = [i + '.SH' if i[0]=='6' else i + '.SZ' for i in x['证券代码']]
    x['持仓'] = (x['持仓'] / 100).round(0).astype(int) * 100
    if pf_code=='5160503':
        price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/pre_close.pkl').loc[open_o32_date]
    else:
        price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/'+open_o32_date+'.pkl').iloc[119]
#     price = x['最新价']
    x_amt = (x['持仓']*price.loc[x['持仓'].index])
    x_amt = x['市值']
    open_position_weight = x_amt/x_amt.sum()
    open_position_weight = open_position_weight.reindex(price.index)
    open_position_weight = open_position_weight.fillna(0)
    capital = x_amt.sum()
#     capital = capital*1.001
    return capital,open_position_weight
def temp(df0,df1):
    v = df0.append(df1)
    return  v.loc[~v.index.duplicated(keep='last')].sort_index()
simulation_w_am = temp(w_am0,w_am)
simulation_w_pm= temp(w_pm0,w_pm)
simulation_w_vwap = temp(w_vwap0,w_vwap)
simulation_w_vwap300 = w_vwap300

pf_code = '5160803'
open_o32_date = '20200601'
o32_path = '/data/user/011477/order/O32/afternoon/'
capital,open_position_weight = get_open_position_w(open_o32_date,pf_code)
simulation_w_pm.loc[open_date] = open_position_weight

pf_code = '5160503'
open_o32_date = '20200515'
o32_path = '/data/user/011477/order/O32/afternoon/'
capital,open_position_weight = get_open_position_w(open_o32_date,pf_code)
simulation_w_vwap.loc[open_o32_date] = open_position_weight

pf_code = '5160304'
open_o32_date = '20200602'
o32_path = '/data/user/011477/order/O32/afternoon/'
capital,open_position_weight = get_open_position_w(open_o32_date,pf_code)
simulation_w_vwap300.loc[open_o32_date] = open_position_weight

print(((simulation_w_vwap - real_w_vwap).abs().sum(axis=1) / 2.).tail())
print(((simulation_w_am - real_w_am).abs().sum(axis=1) / 2.).tail())
print(((simulation_w_pm - real_w_pm).abs().sum(axis=1) / 2.).tail())
print(((simulation_w_vwap300 - real_w_vwap300).abs().sum(axis=1) / 2.).tail())
df = (simulation_w_pm - real_w_pm).abs().loc[today_date]
if (df.sum()>0.001):
    print(today_date,df.sort_values(ascending=False).head(10))
import datetime
today = datetime.date.today().strftime('%Y%m%d')
next_date = today
o32_path = '/data/user/011477/order/O32/morning/'
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
data_end_date = close.index[-1].strftime('%Y%m%d')
today_date = data_end_date
print('today',today)
print('data end date',data_end_date)
hf_open_date = '20200601'
vwap_open_date = '20200515'
vwap300_open_date = '20200602'
def compare_close_weight(index_list,pf_code,backtest_path):
    real_close_w = pd.DataFrame(index = index_list, columns=close.columns, data=0.)
    for d in real_close_w.index.strftime('%Y%m%d'):
        if not os.path.exists(o32_path + '综合信息查询_组合证券' + d + '_516.xls'):
            print(d + ' o32 file missing')
            continue
        x = pd.read_excel(o32_path + '综合信息查询_组合证券' + d + '_516.xls', converters={'组合名称':str, '证券代码':str})
        x = x[(x['组合名称']==pf_code) & (x['证券类别']=='股票')]
        x.index = [i + '.SH' if i[0]=='6' else i + '.SZ' for i in x['证券代码']]
        real_close_w.loc[d, x.index] = x['市值'] / x['市值'].sum()
    real_close_w = real_close_w.shift(-1).fillna(0.).iloc[:-1]
    if pf_code=='5160803':
        test_date_list = simulation_w_pm.loc[hf_open_date:data_end_date].index
        bt = bthf({'0930':simulation_w_am.loc[test_date_list], '1300':simulation_w_pm.loc[test_date_list]}, start_time='1300', 
                  end_time='1300', transaction_period=120, benchmark='ZZ500', capital=5.3e8, 
                  commission=0.0005,simulation=True)
        bt.run()
        save_data(backtest_path,bt.get_stats())
        simulation_close_w = (bt.get_position().loc[(slice(None), '1300'), :].values * close.loc[test_date_list]).fillna(0.)
        simulation_close_w = simulation_close_w.divide(simulation_close_w.sum(axis=1), axis=0)
        print((simulation_w_pm - simulation_close_w).abs().sum(axis=1) / 2.)
    elif pf_code=='5160503':
        test_date_list = simulation_w_vwap.loc[vwap_open_date:data_end_date].index
        print(test_date_list)
        bt = bthf({'0930':simulation_w_vwap.loc[test_date_list]}, start_time='0930', end_time='0930', transaction_period=240, benchmark='ZZ500', 
                  capital=5.3e8, commission=0.0005,simulation=True)
        bt.run()
        save_data(backtest_path,bt.get_stats())
        simulation_close_w = (bt.get_position().loc[(slice(None), '0930'), :].values * close.loc[test_date_list]).fillna(0.)
        simulation_close_w = simulation_close_w.divide(simulation_close_w.sum(axis=1), axis=0)
        print((simulation_w_vwap - simulation_close_w).abs().sum(axis=1) / 2.)

    elif pf_code=='5160304':
        test_date_list = simulation_w_vwap300.loc[vwap300_open_date:data_end_date].index
        print(test_date_list)
        bt = bthf({'0930':simulation_w_vwap300.loc[test_date_list]}, start_time='0930', end_time='0930', transaction_period=240, 
                  benchmark='HS300', capital=2e8, commission=0.0005,simulation=True)
        bt.run()
        save_data(backtest_path,bt.get_stats())
        simulation_close_w = (bt.get_position().loc[(slice(None), '0930'), :].values * close.loc[test_date_list]).fillna(0.)
        simulation_close_w = simulation_close_w.divide(simulation_close_w.sum(axis=1), axis=0)
        print((simulation_w_vwap300 - simulation_close_w).abs().sum(axis=1) / 2.)

    print((simulation_close_w - real_close_w).abs().sum(axis=1) / 2.)
    
    print((simulation_close_w - real_close_w).abs().loc[today_date].sort_values(ascending=False).head(10))
    return simulation_close_w,real_close_w
index_list = real_w_pm.loc[vwap_open_date:].index.tolist() 
if real_w_pm.index[-1]!=pd.Timestamp(next_date):
    index_list = index_list + [pd.Timestamp(next_date)]
close_500 = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close_000905SH.pkl')['close_000905SH']
ret_500 = close_500/close_500.shift(1)-1
from xquant.xqutils.xqfile import FTPFile
ftp = FTPFile()
ftp.downloadFile('516/Alpha/'+today_date+'_Alpha.xlsx', '/data/user/013546/DailyReport/shipan/'+today_date+'_Alpha.xlsx')
flag = True
if flag:
    ftp.downloadFile('516/5160803_QuantMachine_Apollo/Apollo_AMPM_'+today_date+'.xlsx', '/data/user/013546/DailyReport/shipan/5160803_QuantMachine_Apollo/'+today_date+'_5160803_调仓情况.xlsx')
    pf_code_list = ['5160503','5160304']
    for pf_code in pf_code_list:
        ftp.downloadFile('516/'+pf_code+'_QuantMachine_Apollo/'+today_date+'_'+pf_code+'_Apollo.xlsx', 
                     '/data/user/013546/DailyReport/shipan/'+pf_code+'_QuantMachine_Apollo/'+today_date+'_'+pf_code+'_调仓情况.xlsx')
old_compare_file = 'compare/'+last_date+'_Alpha实盘回测对比.xlsx'
compare_file = 'compare/'+today_date+'_Alpha实盘回测对比.xlsx'
pf_code_name={'5160503':('QuantMachine','vwap','0930'),
              '5160803':('AlphaHunter','hf','1300'),
             '5160304':('QuantMachine300','vwap','0930')}
writer = pd.ExcelWriter(compare_file, engine='xlsxwriter')    
for pf_code,v in pf_code_name.items():
    backtest_path = pf_code+'_capital10e7_stats.pkl'
    print(backtest_path)
    simulation_close_w,real_close_w = compare_close_weight(index_list,pf_code,backtest_path)
    compare_weight = (simulation_close_w - real_close_w).abs().sum(axis=1) / 2.
    try:
        compare = pd.read_excel(old_compare_file,index_col=0,sheet_name=pf_code+'_'+v[0])
        compare.index = pd.to_datetime([str(i) for i in compare.index])
    except Exception:
        compare = pd.DataFrame(columns=['实盘回测仓位权重差','实盘超额收益','回测超额收益','现期货敞口收益率','换仓收益率'])
    print(compare)
    compare.loc[pd.to_datetime(today_date),'实盘回测仓位权重差'] = compare_weight.loc[today_date]
    if pf_code=='5160304':
        excess_shipan = pd.read_excel('/data/user/013546/DailyReport/shipan/'+today_date+'_Alpha.xlsx',sheet_name=pf_code+'_QuantMachine300')
    else:
        excess_shipan = pd.read_excel('/data/user/013546/DailyReport/shipan/'+today_date+'_Alpha.xlsx',sheet_name=pf_code+'_QuantMachine500')
    excess_shipan = excess_shipan[['日期','当日Alpha收益率（扣除T0）','现-期货敞口','现货规模']].set_index('日期')
    excess_shipan.index = pd.to_datetime([str(i) for i in excess_shipan.index])
    compare.loc[today_date,'实盘超额收益'] = excess_shipan.loc[today_date].iloc[0]
    excess_backtest = pd.read_pickle(backtest_path)
    excess_backtest = excess_backtest.loc[(slice(None),v[2]),:].reset_index().set_index('level_0')
    excess_backtest.index = pd.to_datetime(excess_backtest.index)
    compare.loc[today_date,'回测超额收益'] = excess_backtest.loc[today_date,'daily_exc']*0.01
    quantile = pd.read_pickle('/data/user/013546/DailyReport/performance/quantile1.pkl')
    if pf_code in ['5160304','5160503']:
        compare.loc[today_date,'模型收益分位数'] = quantile.loc[today_date,'All_vwap']
    else:
        compare.loc[today_date,'上午模型收益分位数'] = quantile.loc[today_date,'All_0930']
        compare.loc[today_date,'下午模型收益分位数'] = quantile.loc[today_date,'All_1300']
    try:
        if pf_code=='5160304':
            excess_backtest_depart = pd.read_pickle('/data/user/013546/AlphaDataCenter/Department/png/benchmark_300/vwap_5d_control_size,turnover10%_capital5e8_amt0.025_turn0.4_w_stats.pkl')
        elif pf_code=='5160803':
            excess_backtest_depart = pd.read_pickle('/data/user/013546/AlphaDataCenter/Department/png/hf_5d_depart_no_control_size,turnover20%_capital5e8_amt0.025_turn0.4_w_stats.pkl')
        else:
            excess_backtest_depart = pd.read_pickle('/data/user/013546/AlphaDataCenter/Department/png/vwap_5d_depart_no_control_size,turnover10%_capital5e8_amt0.025_turn0.4_w_stats.pkl')
        excess_backtest_depart = excess_backtest_depart.loc[(slice(None),v[2]),:].reset_index().set_index('level_0')
        excess_backtest_depart.index = pd.to_datetime(excess_backtest_depart.index)
        compare.loc[today_date,'部门因子回测超额收益'] = excess_backtest_depart.loc[today_date,'daily_exc']*0.01
    except Exception:
        print('depart not exist')
    try:
        compare.loc[today_date,'现期货敞口收益率'] = excess_shipan.loc[last_date,'现-期货敞口']/excess_shipan.loc[last_date,'现货规模']*ret_500.loc[today_date]
        if flag:
            huancang = pd.read_excel('shipan/'+pf_code+'_QuantMachine_Apollo/'+today_date+'_'+pf_code+'_调仓情况.xlsx',sheet_name='汇总',
                           index_col=0,header=0).loc[int(today_date)]
            compare.loc[today_date,'换仓收益率'] = huancang.loc['跑赢均价总金额']/excess_shipan.loc[last_date,'现货规模']
    except Exception:
        print('not exist')
    compare = compare.round(6)
    compare.index = [i.strftime('%Y%m%d') for i in compare.index]
    compare.to_excel(writer,sheet_name = pf_code+'_'+v[0])
    print(pf_code,compare)
writer.close()
print(compare)