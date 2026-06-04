import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, '/data/group/800020/AlphaTools/')
sys.path.insert(0, 'am_update_pf/')
import config_path
from optimize import optimize_hf
import warnings
warnings.filterwarnings("ignore")
from scipy.stats import norm

def get_act_am(last_dt):
    predict = pd.read_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/am/DeepFM_0930_1129_re_1d/%s.csv' % last_dt,header=None)
    act1 = pd.DataFrame(predict[1].values.reshape(1,-1),columns=predict[0].values.tolist())
    predict = pd.read_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/am/LinearRegression_industry_0930_1129_re_5d//%s.csv' % last_dt,header=None)
    act2 = pd.DataFrame(predict[1].values.reshape(1,-1),columns=predict[0].values.tolist())
    predict = pd.read_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/am/XgboostRegression_0930_1129_re_1d/%s.csv' % last_dt,header=None)
    act3 = pd.DataFrame(predict[1].values.reshape(1,-1),columns=predict[0].values.tolist())

    act1_rank = act1.rank(pct=True,axis=1)
    act2_rank = act2.rank(pct=True,axis=1)
    act3_rank = act3.rank(pct=True,axis=1)

    act1_rank[act1_rank==1] = 1-1/3676
    act2_rank[act2_rank==1] = 1-1/3676
    act3_rank[act3_rank==1] = 1-1/3676

    act1_rank[act1_rank==0] = 1/3676
    act2_rank[act2_rank==0] = 1/3676
    act3_rank[act3_rank==0] = 1/3676

    act1_norm = pd.DataFrame(norm.ppf(act1_rank),index=act1.index,columns=act1.columns)
    act2_norm = pd.DataFrame(norm.ppf(act2_rank),index=act2.index,columns=act2.columns)
    act3_norm = pd.DataFrame(norm.ppf(act3_rank),index=act3.index,columns=act3.columns)

    act_mean_am = (act1_norm+act2_norm+act3_norm)/3

    (act_mean_am.T).to_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/am/All/%s.csv' % last_dt,header=None)

def get_act_pm(today_dt):
    predict = pd.read_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/pm/DeepFM_1300_1459_re_1d/%s.csv' % today_dt,header=None)
    act1 = pd.DataFrame(predict[1].values.reshape(1,-1),columns=predict[0].values.tolist())
    predict = pd.read_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/pm/LinearRegression_1300_1459_re_5d/%s.csv' % today_dt,header=None)
    act2 = pd.DataFrame(predict[1].values.reshape(1,-1),columns=predict[0].values.tolist())
    predict = pd.read_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/pm/XgboostRegression_1300_1459_re_1d/%s.csv' % today_dt,header=None)
    act3 = pd.DataFrame(predict[1].values.reshape(1,-1),columns=predict[0].values.tolist())

    act1_rank = act1.rank(pct=True,axis=1)
    act2_rank = act2.rank(pct=True,axis=1)
    act3_rank = act3.rank(pct=True,axis=1)

    act1_rank[act1_rank==1] = 1-1/3676
    act2_rank[act2_rank==1] = 1-1/3676
    act3_rank[act3_rank==1] = 1-1/3676

    act1_rank[act1_rank==0] = 1/3676
    act2_rank[act2_rank==0] = 1/3676
    act3_rank[act3_rank==0] = 1/3676

    act1_norm = pd.DataFrame(norm.ppf(act1_rank),index=act1.index,columns=act1.columns)
    act2_norm = pd.DataFrame(norm.ppf(act2_rank),index=act2.index,columns=act2.columns)
    act3_norm = pd.DataFrame(norm.ppf(act3_rank),index=act3.index,columns=act3.columns)

    act_mean_pm = (act1_norm+act2_norm+act3_norm)/3

    (act_mean_pm.T).to_csv('/data/group/800020/AlphaDataCenter/DailyPrediction/pm/All/%s.csv' % today_dt,header=None)


def load_pf(pf_code, file_path, add_idx_suffix=True):
    df = pd.read_excel(file_path, converters={'组合名称':str, '证券代码':str})
    pf = df[df['组合名称']==pf_code]
    pf.set_index(['证券代码'], inplace=True)
    # pf['市值'] = [float(v.replace(',', '')) for v in pf['市值']]
    # pf['市值'] = pf['市值'].apply(lambda x: float(x.replace(',','')))
    short_ = pf[pf['证券类别']=='股指期货']
    short_.loc[short_['持仓多空标志']=='多仓', ['持仓', '市值']] *= -1
    long_ = pf[pf['证券类别']=='股票']
    if add_idx_suffix:
        long_.index = [i + '.SH' if i[0]=='6' else i + '.SZ' for i in long_.index]
    return pf, long_, short_

def save_xlsx(file_path, sheet_dict):
    writer = pd.ExcelWriter(file_path)
    for k in sheet_dict.keys():
        sheet_dict[k].to_excel(writer, sheet_name=k)
    writer.save()

def exclude_invalid(position, valid_stk):
    pos_valid_stk = list(set(position.index).intersection(valid_stk))
    pos_valid_stk.sort()
    return position[pos_valid_stk]
    
def cal_t0_position(last_position, new_position, valid_position, valid_stk):
    assert np.sum(new_position<0)==0
    last_position = exclude_invalid(last_position, valid_stk)
    new_position = exclude_invalid(new_position, valid_stk)
    
    last_new_stk = list(set(last_position.index).union(new_position.index))
    t0_position = pd.DataFrame(index=last_new_stk, columns=['last', 'new', 'valid'], data=0)
    t0_position.loc[last_position.index, 'last'] = last_position
    t0_position.loc[new_position.index, 'new'] = new_position
    assert len(set(last_position.index)-set(valid_position.index))==0
    t0_position.loc[last_position.index, 'valid'] = valid_position[last_position.index]
    t0_position = t0_position.min(axis=1)
    t0_position = t0_position[t0_position>=100]
    t0_position.sort_index(inplace=True)
    return t0_position

def generate_t0_xlsx(t0_position, pf_code, today, time):
    assert np.sum(t0_position<=0)==0
    t0_position.index.name = '证券代码'
    t0_xlsx = pd.DataFrame(index=t0_position.index, 
                           columns=['买入交易账户', '卖出交易账户', '证券额度'], 
                           data=np.nan)

    t0_xlsx['买入交易账户'] = int(pf_code)
    t0_xlsx['卖出交易账户'] = int(pf_code)
    if pf_code=='5160501':
        t0_xlsx['买入交易账户'] = pf_code + 'l'
        t0_xlsx['卖出交易账户'] = pf_code + 'l'
    t0_xlsx['证券额度'] = t0_position
    
    t0_xlsx.to_excel(config_path.generate_pf_data_path+'t0_position/' + pf_code + '_日内可用额度_' + today + '_' + time + '.xlsx')
    
    return t0_xlsx

def cal_reb_position(last_position, new_position, valid_position, valid_stk):
    assert np.sum(new_position<0)==0
    last_position = exclude_invalid(last_position, valid_stk)
    new_position = exclude_invalid(new_position, valid_stk)
    
    last_new_stk = list(set(last_position.index).union(new_position.index))
    reb_position = pd.Series(index=last_new_stk, data=0)
    reb_position[new_position.index] = new_position
    reb_position[last_position.index] -= last_position
    sell_stk = reb_position[reb_position<0].index
    reb_position[sell_stk] = np.maximum(reb_position[sell_stk], -valid_position[sell_stk])
    reb_position = (reb_position / 100).astype(int) * 100
    reb_position = reb_position[reb_position!=0]
    reb_position.sort_index(inplace=True)
    return reb_position

def generate_reb_xlsx(reb_position, pf_code, today, time):
    assert np.sum(reb_position==0)==0
    reb_position.index.name = '证券代码'
    reb_xlsx = pd.DataFrame(index=reb_position.index, 
                            columns=['委托方向', '指令数量', '指令价格', '价格模式', '市场代码'], 
                            data=np.nan)
    buy_stk = reb_position[reb_position>0].index.tolist()
    sell_stk = reb_position[reb_position<0].index.tolist()
    reb_xlsx.loc[buy_stk, '委托方向'] = 1
    reb_xlsx.loc[sell_stk, '委托方向'] = 2
    assert np.sum(np.isnan(reb_xlsx['委托方向']))==0
    reb_xlsx['指令数量'] = reb_position.abs()
    reb_xlsx['指令价格'] = 0
    reb_xlsx['价格模式'] = 4
    sh_stk = [i for i in reb_position.index if i[-2:]=='SH']
    sz_stk = [i for i in reb_position.index if i[-2:]=='SZ']
    reb_xlsx.loc[sh_stk, '市场代码'] = 1
    reb_xlsx.loc[sz_stk, '市场代码'] = 2
    reb_xlsx = reb_xlsx.astype(int)
    
    reb_xlsx.to_excel(config_path.generate_pf_data_path+'reb_position/' + pf_code + '_下单指令_' + today + '_' + time + '.xlsx')
    
    return reb_xlsx

def generate_close_xlsx(reb_position, pf_code, today, close_after_open):
    assert np.sum(reb_position==0)==0
    reb_position.index.name = '证券代码'
    reb_xlsx = pd.DataFrame(index=reb_position.index, 
                            columns=['委托方向', '指令数量', '指令价格', '价格模式', '市场代码'], 
                            data=np.nan)
    reb_xlsx['委托方向'] = 2
    assert np.sum(np.isnan(reb_xlsx['委托方向']))==0
    reb_xlsx['指令数量'] = reb_position.abs()
    reb_xlsx['指令价格'] = 0
    reb_xlsx['价格模式'] = 4
    sh_stk = [i for i in reb_position.index if i[-2:]=='SH']
    sz_stk = [i for i in reb_position.index if i[-2:]=='SZ']
    reb_xlsx.loc[sh_stk, '市场代码'] = 1
    reb_xlsx.loc[sz_stk, '市场代码'] = 2
    reb_xlsx.index = [i[:-3] for i in reb_xlsx.index]
    reb_xlsx = reb_xlsx.astype(int)
    
    after = ''
    if close_after_open:
        after = '盘中'
    reb_xlsx.to_excel(config_path.generate_pf_data_path+'close_position/' + pf_code + '_下单指令_' + after + '平仓_' + today + '.xls')
    
    return reb_xlsx

def format_weight(w, pf_code, today, time, open_position=False):
    assert np.sum(w<0)==0
    w = (w[w>0] * 100) / w[w>0].sum()
    w.index = [i[:-3]  for i in w.index]
    
    qpool = pd.read_excel(config_path.generate_pf_data_path+'others/quant_pool.xls', converters={'证券名称':str, '证券代码':str})
    qpool.index = qpool['证券代码']
    qpool.index.name = None
    
    ################### to delete ###################
    # w = w.drop(sorted(set(w.index)-set(qpool.index)))  
    # w = (w[w>0] * 100) / w[w>0].sum()
    ################### to delete ###################
    
    assert len(set(w.index)-set(qpool.index))==0
    
    qpool.loc[w.index.tolist(), '权重'] = w
    qpool['市场名称'] = [1 if s[0]=='6' else 2 for s in qpool['证券代码']]
    
    formatted_w = qpool[pd.notnull(qpool['权重'])]
    formatted_w = formatted_w[['证券代码', '证券名称', '市场名称', '权重']]
    file_name = config_path.generate_pf_data_path+'reb_weight/' + pf_code + '_weight_' + today + '.xlsx'
    if open_position:
        file_name = config_path.generate_pf_data_path+'open_weight/' + pf_code + '_weight_open_' + today + '_' + time + '.xlsx'
    formatted_w.to_excel(file_name)
    return formatted_w

def pf_generator(today_act, time, last_position, valid_position, valid_stk, pf_code, turn_ad, hedge_index, capital, cash, barra_limit_dict, industry_loose, dupl_industry, split_fin):
    
    left_stk = last_position[last_position<100].index.tolist()
    rebalance_stk = last_position[last_position>=100].index.tolist()
    assert np.sum(last_position[rebalance_stk]<100)==0
    
    today = today_act.index[0]
    today_dt = today.strftime('%Y%m%d')
    close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
    close.loc[today] = np.nan
    close = close.shift(1).loc[today]
    assert np.sum(np.isnan(close[rebalance_stk].values))==0
    
    asset = cash + (last_position[rebalance_stk] * close[rebalance_stk]).sum()
    assert asset>0
    last_weight = pd.Series(index=close.index, data=0.)
    last_weight[rebalance_stk] = (last_position[rebalance_stk] * close[rebalance_stk]) / asset
    
    if time=='1300':
        close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/' + today_dt + '.pkl').iloc[119]
    lower_limit = pd.Series(index=close.index, data=0.)
    lower_limit[rebalance_stk] = last_weight[rebalance_stk] - valid_position[rebalance_stk] * close[rebalance_stk] / asset
    
    if time=='0930':
        assert np.abs(lower_limit.sum())<0.000001, 'lower limit error'

    w = optimize_hf({time:today_act}, {time:turn_ad}, hedge_index, capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, 
                     dupl_industry=dupl_industry, split_fin=split_fin, prev_weights=last_weight, lower_limit=lower_limit,amt_limit=0.1, pool_valid_stocks=valid_stk)
    
    today_dt = today.strftime(format='%Y%m%d')
    w = w[time].loc[today]
    assert np.sum(w<0)==0
    assert np.sum(w[pd.isnull(close)]!=0)==0
    assert np.sum(np.isinf(w))==0
    assert np.sum(np.isnan(w))==0
    fw = format_weight(w, pf_code, today_dt, time)
    
    print('sum of weight:', w.sum())
    print('sum of adjusted weight:', fw['权重'].sum(), '<= 100 ?', str(fw['权重'].sum()<=100))
    
    today_position = ((w * asset) / close).fillna(0).astype(int)
    today_position[left_stk] += last_position[left_stk]
    assert np.sum(today_position<0)==0
    assert np.sum(np.isnan(today_position))==0
    assert np.sum(np.isinf(today_position))==0
    today_position = today_position[today_position>0]
    
    return today_position, w, fw




def reb_to_dupl_index(last_position, cash, valid_stk, today_weight, today_dt, pf_code):
    
    left_stk = last_position[last_position<100].index.tolist()
    rebalance_stk = last_position[last_position>=100].index.tolist()
    #if pf_code=='5160504':
    #    invalid_stk = ['000333.SZ', '603156.SH', '601066.SH', '601838.SH', '601828.SH', '603259.SH', '601138.SH', '002925.SZ', '601598.SH', '600901.SH']
    #elif pf_code=='5160803':
    #    invalid_stk = ['601598.SH']
    invalid_stk = []
    left_stk = sorted(set(left_stk) - set(invalid_stk))
    rebalance_stk = sorted(set(rebalance_stk) - set(invalid_stk))
    assert np.sum(last_position[rebalance_stk]<100)==0
    
    today = pd.Timestamp(today_dt)
    close = pd.read_pickle('/app/HTSCAlpha/AlphaDataCenter/Basic/daily/close.pkl')
    close.loc[today] = np.nan
    close = close.shift(1).loc[today]
    assert np.sum(np.isnan(close[rebalance_stk].values))==0
    
    asset = cash + (last_position[rebalance_stk] * close[rebalance_stk]).sum()
    assert asset>0
    last_weight = pd.Series(index=close.index, data=0.)
    last_weight[rebalance_stk] = (last_position[rebalance_stk] * close[rebalance_stk]) / asset

    w = today_weight
    assert np.sum(w<0)==0
    assert np.sum(w[pd.isnull(close)]!=0)==0
    assert np.sum(np.isinf(w))==0
    assert np.sum(np.isnan(w))==0
    fw = format_weight(w, pf_code, today_dt, time)
    
    print('sum of weight:', w.sum())
    print('sum of adjusted weight:', fw['权重'].sum(), '<= 100 ?', str(fw['权重'].sum()<=100))

    today_position = ((w * asset) / close).fillna(0).astype(int)

    today_position[left_stk] += last_position[left_stk]
    assert np.sum(today_position<0)==0
    assert np.sum(np.isnan(today_position))==0
    assert np.sum(np.isinf(today_position))==0
    today_position = today_position[today_position>0]
    
    return today_position, w, fw



