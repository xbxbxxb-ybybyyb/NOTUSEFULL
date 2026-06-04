import os
import numpy as np
import pandas as pd
import cvxpy as cvx
import warnings
warnings.filterwarnings("ignore")

def optimize_hf(act_dict,turnover_adversion_dict,hedge_index='ZZ500',capital=500000000.,barra_limit_dict={},industry_loose = 1000,
                single_stock_max_weight=0.01,amt_limit=0.025,amt_limit_window=5,prev_weights=None,lower_limit=None,pool_valid_stocks=None,
                dupl_industry=[6133,613401,613402,613403],split_fin=True):
    rebalance_times = sorted(act_dict.keys())
    optimizing_dates = act_dict[rebalance_times[0]].index
    if len(rebalance_times)>1:
        for i in range(1,len(rebalance_times)):
            assert len(set(optimizing_dates)-set(act_dict[rebalance_times[i]].index))==0,rebalance_times[i]+' act lack of '+str(set(optimizing_dates)-set(act_dict[rebalance_times[i]].index))
    ######################################### section 1  load data
    data_center_path = '/data/group/800020/AlphaDataCenter/'
    basic_daily_path = data_center_path + 'Basic/daily/'
    factor_barra_path = data_center_path + 'Factor/barra/'

    index_weights = pd.read_pickle(basic_daily_path + hedge_index + '_data.pkl') / 100
    index_weights = index_weights.divide(index_weights.sum(axis=1), axis=0)
    industry_code_df = pd.read_pickle(basic_daily_path + 'swX_industry_code.pkl').astype(np.float64)
    industry_code_df[industry_code_df==613301] = 6133    # bank
    industry_code_df[industry_code_df==611902] = 6133    # bank
    industry_code_df[industry_code_df==611903] = 613401  # securities company
    industry_code_df[industry_code_df==611904] = 613402  # insurance
    industry_code_df[industry_code_df==611901] = 613403  # other financial company
    if not split_fin:
        industry_fin_position = np.logical_or(np.logical_or(industry_code_df==613401, industry_code_df==613402), 
                                              industry_code_df==613403)
        industry_code_df[industry_fin_position] = 6134
    industry_list = sorted(industry_code_df.stack().unique().tolist())

    pre_close = pd.read_pickle(basic_daily_path + 'pre_close.pkl')
    close = pd.read_pickle(basic_daily_path + 'close.pkl')
    vwap_adj = pd.read_pickle(basic_daily_path + 'vwap_adj.pkl')
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
    is_valid_forward1 = pd.read_pickle(basic_daily_path + 'is_valid.pkl').shift(1)
    is_valid_raw = pd.read_pickle(basic_daily_path + 'is_valid_raw.pkl')
    is_valid_raw_st = pd.read_pickle(basic_daily_path + 'isValid_raw_incl_st.pkl')
    st = (is_valid_raw_st - is_valid_raw).fillna(0)
    amt = pd.read_pickle(basic_daily_path + 'amt.pkl')
    avg_amt = (amt[is_valid_raw_st==1].rolling(window=amt_limit_window).mean()*1000).fillna(1e7)

    # donot rebalance weights if is_valid_count/is_valid_count_max_prev_5d < 0.8 in 2015
    is_valid_count = is_valid.sum(axis=1)
    is_valid_count_max_prev_5d = is_valid_count.rolling(window=5, min_periods=1).max().shift(1).fillna(method='bfill')


    index_industry_total_weight_df = {}    # total weights dataframe of index for each industry, index=dates, columns=industry_codes
    industry_stock_dict = {}               # industry code dataframe of all stocks for each industry, index=dates, columns=all_stocks
    for industry in industry_list:
        this_industry_stock_df = pd.DataFrame(0., index=industry_code_df.index, columns=industry_code_df.columns)
        this_industry_stock_df[industry_code_df==industry] = 1
        industry_stock_dict[industry] = this_industry_stock_df
        index_industry_total_weight_df[industry] = (index_weights*this_industry_stock_df).sum(axis=1)
    index_industry_total_weight_df = pd.DataFrame(index_industry_total_weight_df)


    barra_factor_names =  ['Beta'+hedge_index[-3:],'EarningsYield','Growth','Leverage','Liquidity','Momentum','Size','Value','Volatility']

    barra_dict = {}        # barra dataframe of all stocks for each barra factor
    for factor in barra_factor_names:
        barra_dict[factor] = pd.read_pickle(factor_barra_path + factor + '.pkl')
    barra_factor = pd.DataFrame({k:v.stack(dropna=False) for k,v in barra_dict.items()})
    index_barra_df = {}    # barra dataframe of index, index=dates, columns=barra_factor_names
    for factor in barra_factor_names:
        index_barra_df[factor] = (index_weights*barra_dict[factor]).sum(axis =1)
    index_barra_df = pd.DataFrame(index_barra_df)
    
    ######################################### section 2  set parameters
    # capital 为计算冲击成本和冲击限制用到的，照实际填写
    # industry_loose 行业中性的松紧，组合某一行业权重在（index 该行业权重 ± industry_loose ）之间
    # single_stock_max_weight 为单只股票最大持有比例
    # turnover_adversion 为对换手的惩罚，按照各自 prediction 值不同做调整
    # impact_adversion 为对冲击的惩罚，是原公式中万分之1.2乘以调整数（100），与其他 adversion 调整相同
    # risk_adversion 为对波动的惩罚，（调的过大可能导致优化器出现 Numerical Error，我最大试到50）
    # barra_limit_dict 为对各个大类风格的宽松上下界，组合某一风格权重在（index 该风格权重 - barra_limit_dict[风格][0]）与（index该风格权重 - barra_limit_dict[风格][1]）之间
    # 注意14年申万行业进行过大变更，会影响波动限制部分 Factor_return 部分，建议14年之前和14年之后分别进行优化，不要连在一起，具体日期要查一下，从那一天开始平安银行000001.SZ行业变了
    ######################################### Section 3  optimize
    
    trading_pool_dates = None

    his_dates = close.index.tolist()
    all_stocks = close.columns.tolist()
    if pool_valid_stocks is None:
        pool_valid_stocks = close.columns.tolist()
        trading_pool_dates = np.array(sorted([abc[-12:-4] for abc in os.listdir('/data/user/011477/order/O32/pool/') if abc.find('trading_pool_')==0]))

    my_2015_his_dates = close.loc['20150101':'20151231'].index.tolist()

    w0 = np.zeros(len(all_stocks))
    if prev_weights is not None:
        w0 = prev_weights.loc[all_stocks].fillna(0).values
    w0 = np.matrix(w0).T

    lower_w = np.zeros(len(all_stocks))
    if lower_limit is not None:
        lower_w = lower_limit.loc[all_stocks].fillna(0).values

    optimized_weights_list = []
    optimized_stocks_list = []
    
    multi_date_portfolio_weight = {}
    prev_portfolio_weight = pd.Series(index=all_stocks,data=np.array(w0).flatten())
    for date in optimizing_dates:
        # see if date is the very previous date
        if date in his_dates:
            prev_date=his_dates[his_dates.index(date)-1]
        else:
            prev_date=his_dates[-1]
            print("should be the very new day to be optimized")
        
        # date_valid_stocks
        date_valid_stocks_all = sorted(set(pool_valid_stocks) - set(['000018.SZ']))
        
        if trading_pool_dates is not None and trading_pool_dates[0]<date.strftime('%Y%m%d'):
            trading_pool_date = trading_pool_dates[date.strftime('%Y%m%d') > trading_pool_dates][-1]
            print('trading pool date : ', trading_pool_date)
            trading_pool_stk = pd.read_excel('/data/user/011477/order/O32/pool/trading_pool_' + trading_pool_date + '.xls', converters={'证券代码':str})['证券代码']
            trading_pool_stk = [abc + '.SH' if abc[0]=='6' else abc + '.SZ' for abc in trading_pool_stk.values]
            # date_valid_stocks_all = sorted(set(date_valid_stocks_all) & set(trading_pool_stk))
            non_pool_stk = sorted(set(all_stocks) - set(trading_pool_stk))
            non_pool_to_sell_stk = sorted(set(prev_portfolio_weight[prev_portfolio_weight>0.].index.tolist()) & set(non_pool_stk))
            non_pool_invalid_stk = sorted(set(prev_portfolio_weight[prev_portfolio_weight<=0.].index.tolist()) & set(non_pool_stk))
            date_valid_stocks_all = sorted(set(date_valid_stocks_all) - set(non_pool_invalid_stk))
            for tt in rebalance_times:
                act_dict[tt].loc[date, non_pool_stk] = np.nan
        
        if date in his_dates:
            date_is_valid_raw = is_valid_raw_st.loc[date]
            date_trading_stocks = date_is_valid_raw[date_is_valid_raw==1].index.tolist()
            date_valid_stocks_all = sorted(set(date_valid_stocks_all).intersection(date_trading_stocks))
        
        if date not in my_2015_his_dates or (is_valid_count[date]/is_valid_count_max_prev_5d[date])>=0.8 or date==optimizing_dates[0]:
            rebalance = True
        
        # date data
        date_avg_amt = avg_amt.loc[prev_date]
        date_index_weight = index_weights.loc[prev_date]
        date_industry_code = industry_code_df.loc[prev_date]
        date_index_indus_weight = index_industry_total_weight_df.loc[prev_date]
        date_index_barra = index_barra_df.loc[prev_date]
        date_barra_factor = barra_factor.loc[prev_date]
        # assert if industry codes of index stocks are nan
        index_stock_wo_industry_code_idx = np.logical_and(date_index_weight>0, pd.isnull(date_industry_code))
        if index_stock_wo_industry_code_idx.sum()>0:
            print(date_index_weight.loc[index_stock_wo_industry_code_idx])
            raise AssertionError(str(prev_date)+' , the above stock in '+hedge_index+' has no industry code')

            
        today_buy_portfolio_weight = pd.Series(index=all_stocks,data=lower_w)
        last_time_portfolio_weight = prev_portfolio_weight
        for time in rebalance_times:
            print(time)
            if date in his_dates:
                if time=='0930':
                    close_ = close.loc[prev_date]
                    pre_close_ = pre_close.loc[prev_date]
                    st_ = st.loc[prev_date]
                else:
                    close_ = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/' + date.strftime('%Y%m%d') + '.pkl').iloc[119]
                    pre_close_ = pre_close.loc[date]
                    st_ = st.loc[date]
                returns = close_ / pre_close_ - 1.
                maxup_stk = (returns[(returns >= 0.098) | ((returns >= 0.048) & (st_ == 1))]).index.tolist()
                maxdown_stk = (returns[(returns <= -0.098) | ((returns <= -0.048) & (st_ == 1))]).index.tolist()

                date_valid_stocks = sorted(set(date_valid_stocks_all) - set(maxup_stk) - set(maxdown_stk))

            else:
                date_valid_stocks = date_valid_stocks_all
            
            ## adjust industry weight of invalid stocks in prev portfolio that exceeds index
            prev_portfolio_weight = adjust_excess_index_indus_weight(prev_portfolio_weight,date_industry_code,date_index_indus_weight,date_valid_stocks)

            # dupl_industry adjust weight
            dupl_industry_weights = {}
            if hedge_index in ['HS300', 'ZZ800'] and dupl_industry is not None:
                dupl_industry_weights = get_dupl_industry_weight(prev_date,dupl_industry,date_valid_stocks,prev_portfolio_weight,date_index_weight, date_industry_code,date_index_indus_weight)
                
            date_act_series = act_dict[time].loc[date]
            date_act_series = date_act_series.reindex(index=date_index_weight.index)
            date_act_series[np.isinf(date_act_series)] = np.nan
            single_stock_min_weight_series = today_buy_portfolio_weight
            turnover_adversion_ = turnover_adversion_dict[time]
            this_time_portfolio_weight = get_weights(date,date_act_series,last_time_portfolio_weight,date_valid_stocks,
                                  date_avg_amt,capital,date_industry_code,date_index_indus_weight,pd.get_dummies(date_industry_code),
                                  date_index_barra,date_barra_factor,
                                  barra_limit_dict,industry_loose,turnover_adversion_,single_stock_min_weight_series,single_stock_max_weight,amt_limit,
                                  rebalance=rebalance,dupl_industry_weights=dupl_industry_weights)
            today_buy_portfolio_weight += np.maximum(this_time_portfolio_weight-last_time_portfolio_weight,0)
            last_time_portfolio_weight = this_time_portfolio_weight
            if not time in multi_date_portfolio_weight:
                multi_date_portfolio_weight[time] = {}
            multi_date_portfolio_weight[time][date] = this_time_portfolio_weight

        prev_portfolio_weight = last_time_portfolio_weight.copy()
    return {k:pd.DataFrame(v).T for k,v in multi_date_portfolio_weight.items()}

def adjust_excess_index_indus_weight(prev_portfolio_weight,industry_code,index_indus_weight,valid_stocks):
    date_invalid_stocks_in_prev_portfolio = list(set(prev_portfolio_weight[prev_portfolio_weight>0].index) - set(valid_stocks))
    portfolio_weights_industry_code_df = pd.DataFrame(index=['weight', 'industry'], data=[prev_portfolio_weight, industry_code]).T
    portfolio_invalid_stocks_weights_industry_code_df = portfolio_weights_industry_code_df.loc[date_invalid_stocks_in_prev_portfolio]
    portfolio_invalid_stocks_industry_total_weight_series = portfolio_invalid_stocks_weights_industry_code_df.groupby('industry').sum()['weight']
    diff_portfolio_invalid_stocks_index_industry_total_weight = portfolio_invalid_stocks_industry_total_weight_series - index_indus_weight.loc[portfolio_invalid_stocks_industry_total_weight_series.index]
    invalid_excess_index_industry_list = diff_portfolio_invalid_stocks_index_industry_total_weight[diff_portfolio_invalid_stocks_index_industry_total_weight>0].index.tolist()
    if len(invalid_excess_index_industry_list)>0:
        print('warning: excess index industry weight due to invalid stock weights')
        print(invalid_excess_index_industry_list)
        print()
    for industry in invalid_excess_index_industry_list:
        print(industry)
        invalid_excess_index_industry_stocks = set(prev_portfolio_weight[industry_code==industry].index).intersection(date_invalid_stocks_in_prev_portfolio)
        prev_portfolio_weight[invalid_excess_index_industry_stocks] *= (index_indus_weight.loc[industry] / portfolio_invalid_stocks_industry_total_weight_series[industry])
    return prev_portfolio_weight

def get_dupl_industry_weight(prev_date,dupl_industry,valid_stocks,
                             portfolio_weight,index_weight,industry_code,index_indus_weight):
    print('adjust duplicate industry stock weight')
    dupl_industry_weight = {}
    for k in dupl_industry:
        index_dupl_industry_stocks_flag = np.logical_and(industry_code==k, index_weight>0)
        index_dupl_industry_valid_stocks = list(set(index_dupl_industry_stocks_flag[index_dupl_industry_stocks_flag].index.tolist()).intersection(valid_stocks))
        # assert if all stocks in hedge index and industry k are invalid
        if len(index_dupl_industry_valid_stocks)==0:
            raise AssertionError(str(prev_date)+', abnormality: all '+' stocks of industry '+str(k)+' are invalid')
        portfolio_dupl_industry_stocks_idx = np.logical_and(industry_code==k, portfolio_weight>0)
        portfolio_dupl_industry_invalid_stocks = list(set(portfolio_weight[portfolio_dupl_industry_stocks_idx].index) - set(valid_stocks))
                
        portfolio_dupl_industry_invalid_stocks_total_weight = portfolio_weight.loc[portfolio_dupl_industry_invalid_stocks].sum()
        # assert if total weight of invalid stocks in prev portfolio and industry k is greater than total weight of industry k of hedge index
        if portfolio_dupl_industry_invalid_stocks_total_weight>index_indus_weight[k]:
            raise AssertionError(str(prev_date)+', total weight of invalid stock in '+str(k)+', '+str(portfolio_dupl_industry_invalid_stocks_total_weight)+
                                 ', exceeds total weight of '+str(k)+', '+str(index_indus_weight))

        adjust_total_weight = index_indus_weight.loc[k] - portfolio_dupl_industry_invalid_stocks_total_weight
        dupl_industry_weight[k] = (index_weight.loc[index_dupl_industry_valid_stocks] / index_weight.loc[index_dupl_industry_valid_stocks].sum()) * adjust_total_weight
        dupl_industry_weight[k] = dupl_industry_weight[k].round(10)
    assert len(set(dupl_industry_weight.keys()) - set(dupl_industry))==0, 'missing adjusted industry weight'
    return dupl_industry_weight

def get_weights(date,date_act_series,prev_portfolio_weight,valid_stocks,
                avg_amt,capital,industry_code,
                index_indus_weight,industry_stock,
                index_barra,barra_stock,
                barra_limit_dict,industry_loose,turnover_adversion,
                single_stock_min_weight_series=None,single_stock_max_weight=0.001,amt_limit=0.025,
                rebalance=True,dupl_industry_weights={}):
    all_stocks = date_act_series.index
    w0 = np.zeros(len(all_stocks))
    if prev_portfolio_weight is not None:
        w0 = prev_portfolio_weight.loc[all_stocks].fillna(0).values
    # w0 = np.matrix(w0).T
    optimized_weights_list = []
    optimized_stocks_list = []
    w = cvx.Variable(len(all_stocks),nonneg=True)
    expected_return = date_act_series.fillna(-50).values.astype(np.float64)
    objective = cvx.Maximize(expected_return.T@w- turnover_adversion * cvx.sum(cvx.elementwise.abs.abs(w-w0)))

    constraints = []
    constraints.append(cvx.sum(w)==1)

    lower_bound = []
    upper_bound = []
    for stock in all_stocks:
        # amt_bound = avg_amt.loc[stock] * 0.025 / capital#@
        amt_bound = avg_amt.loc[stock] * amt_limit / capital
        up_bound = 0
        if not single_stock_min_weight_series is None:
            up_bound = single_stock_min_weight_series.loc[stock]
        bound = (up_bound, min(single_stock_max_weight, amt_bound))
        if up_bound>min(single_stock_max_weight, amt_bound):
            bound = (up_bound, up_bound)
        stock_industry_code = industry_code.loc[stock]

        # if stock is to be duplicated
        if (stock_industry_code in dupl_industry_weights):
            if (stock in dupl_industry_weights[stock_industry_code]) and (dupl_industry_weights[stock_industry_code].loc[stock]>0.00001):
                bound = (dupl_industry_weights[stock_industry_code].loc[stock]-0.00001, 
                         dupl_industry_weights[stock_industry_code].loc[stock]+0.00001)
            else:
                bound = (0, 0)

        if stock not in valid_stocks:
            if prev_portfolio_weight.loc[stock]>0:
                bound = (prev_portfolio_weight.loc[stock], prev_portfolio_weight.loc[stock])
            else:
                bound = (0, 0)

        lower_bound.append(max(bound[0],up_bound))
        upper_bound.append(bound[1])
    constraints.append(w >= lower_bound)
    constraints.append(w <= upper_bound)

    # industry constraintsa
    index_indus_weight = index_indus_weight[index_indus_weight!=0]
    for industry in index_indus_weight.index:
        industry_values = industry_stock[industry].values
        upper_bound = index_indus_weight.loc[industry] + industry_loose
        lower_bound = index_indus_weight.loc[industry] - industry_loose
        constraints.append(industry_values * w >= lower_bound)
        constraints.append(industry_values * w <= upper_bound)

    # barra constraints

    for factor in barra_limit_dict.keys():
        barra_values = barra_stock[factor].fillna(0).values
        lower_bound = index_barra.loc[factor]/1.0 - barra_limit_dict[factor][0]
        upper_bound = index_barra.loc[factor]/1.0 + barra_limit_dict[factor][1]
        constraints.append(barra_values * w >= lower_bound)
        constraints.append(barra_values * w <= upper_bound)
    
    prob = cvx.Problem(objective, constraints)

    try:
        maximum_activition = prob.solve(verbose=False, solver=cvx.ECOS, reltol=0.001)
    except:
        print(date, ' SolverError!!!')
        return None
    else:
        if maximum_activition==np.inf or maximum_activition==-np.inf:
            print(date, 'No solution')
            optimized_weights_list.append([])
            optimized_stocks_list.append([])
        else:
            if rebalance:
                weight_today = pd.Series(np.array(w.value), index=all_stocks)
            else:
                print(str(date) + ', portfolio weights not rebalanced')
            print(date, 'select stocks number: ', len(weight_today[weight_today>0.00001]))
            weight_today[weight_today<=0.00001] = 0
            weight_today = weight_today.round(10)
            optimized_weights_list.append(weight_today.values)
            optimized_stocks_list.append(weight_today.index)
            return weight_today

import pandas as pd
am = pd.read_pickle('/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/am/All_5d.pkl')
pm = pd.read_pickle('/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/pm/All_5d.pkl')
vwap = pd.read_pickle('/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/vwap/All_5d.pkl')
start_date = '20190103'
hf_model={}
hf_model['0930'] = am.shift(1).iloc[1:]
hf_model['1300'] = pm.loc[start_date:]
vwap_model={}
vwap_model['0930'] = vwap.shift(1).iloc[1:]
capital_dict={'vwap':(2e8,'2e8'),
             'hf':(5e8,'5e8')}
t='vwap'
hedge_index = 'HS300'
benchmark = hedge_index[-3:]
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
industry_loose = 0.005
amt_limit = 0.025
dupl_industry=[6133,6134]
split_fin=False
pool_valid_stocks=None
barra_limit_dict = {
    'Beta'+benchmark: (0.05, 0.05), 
    'Momentum':              (0.05, 0.05), 
    'Size':                  (0.5, 0.5), 
    'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
w_path_dict = {
                'benchmark'+benchmark+'_5d_no_control_size,turnover20%':(0.4,0.5)
              }
open_close_list=[('20200101','20200529')]
k = 'benchmark'+benchmark+'_5d_no_control_size,turnover20%'
v = w_path_dict[k]
for open_close_date in open_close_list:
    open_date = open_close_date[0]
    close_date = open_close_date[1]
    print(open_date,close_date)
#     turn_ad={'0930':v[0],'1300':v[0]}
    turn_ad = {'0930':v[0]}
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    last_weight_hf = None
    w_today = optimize_hf({k:v.loc[open_date:close_date] for k,v in vwap_model.items()}, turn_ad, hedge_index, capital, 
                          barra_limit_dict=barra_limit_dict,
                          industry_loose=industry_loose, 
                          amt_limit=amt_limit, 
          prev_weights=last_weight_hf, pool_valid_stocks=None, dupl_industry=dupl_industry, split_fin=False)
pd.to_pickle(w_today,'/data/user/013546/rubbish/test_w.pkl')