# uncompyle6 version 3.7.3
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.5 (default, Jul 28 2020, 12:59:40) 
# [GCC 9.3.0]
# Embedded file name: /data/user/012316/PF/optimize.py
# Compiled at: 2021-02-23 17:40:48
# Size of source mod 2**32: 33745 bytes
import os, numpy as np, pandas as pd, cvxpy as cvx, warnings, copy, time as tm
warnings.filterwarnings('ignore')

class HFOptimizer:

    def __init__(self, save_path):
        self.data_center_path = '/data/group/800020/AlphaDataCenter/'
        self.basic_daily_path = self.data_center_path + 'Basic/daily/'
        self.factor_barra_path = self.data_center_path + 'Factor/barra/'
        self.save_path = save_path

    def LoadRebalanceTime(self, act_dict):
        rebalance_times = sorted(act_dict.keys())
        optimizing_dates = act_dict[rebalance_times[0]].index
        if len(rebalance_times) > 1:
            for i in range(1, len(rebalance_times)):
                assert len(set(optimizing_dates) - set(act_dict[rebalance_times[i]].index)) == 0, rebalance_times[i] + ' act lack of ' + str(set(optimizing_dates) - set(act_dict[rebalance_times[i]].index))

        return (
         rebalance_times, optimizing_dates)

    def LoadIndexWeight(self, simulate_label, hedge_index):
        if simulate_label is True:
            index_weights = pd.read_pickle(self.basic_daily_path + hedge_index + '_data.pkl') / 100
        else:
            index_weights = pd.read_pickle(self.basic_daily_path + hedge_index + '_data_estimate.pkl') / 100
        index_weights = index_weights.divide(index_weights.sum(axis=1), axis=0)
        return index_weights

    def LoadPV(self, amt_limit_window, hedge_index, index_weights, industry_code_df):
        pre_close = pd.read_pickle(self.basic_daily_path + 'pre_close.pkl')
        close = pd.read_pickle(self.basic_daily_path + 'close.pkl')
        vwap_adj = pd.read_pickle(self.basic_daily_path + 'vwap_adj.pkl')
        is_valid = pd.read_pickle(self.basic_daily_path + 'is_valid.pkl')
        is_valid_forward1 = pd.read_pickle(self.basic_daily_path + 'is_valid.pkl').shift(1)
        is_valid_raw = pd.read_pickle(self.basic_daily_path + 'is_valid_raw.pkl')
        is_valid_raw_st = pd.read_pickle(self.basic_daily_path + 'isValid_raw_incl_st.pkl')
        st = pd.read_pickle(self.basic_daily_path + 'stpt.pkl').astype('float')
        amt = pd.read_pickle(self.basic_daily_path + 'amt.pkl')
        avg_amt = (amt[(is_valid_raw_st == 1)].rolling(window=amt_limit_window).mean() * 1000).fillna(10000000.0)
        is_valid_count = is_valid.sum(axis=1)
        is_valid_count_max_prev_5d = is_valid_count.rolling(window=5, min_periods=1).max().shift(1).fillna(method='bfill')
        barra_factor, index_barra_df = self.get_index_barra(self.factor_barra_path, hedge_index, index_weights)
        index_industry_total_weight_df = self.get_index_indus_weight(index_weights, industry_code_df)
        return (
         pre_close, close, vwap_adj, is_valid, is_valid_forward1, is_valid_raw, is_valid_raw_st, st, amt, avg_amt, is_valid_count, is_valid_count_max_prev_5d, barra_factor, index_barra_df, index_industry_total_weight_df)

    def LoadIndustry(self, split_fin):
        industry_code_df = pd.read_pickle(self.basic_daily_path + 'swX_industry_code.pkl').astype(np.float64)
        industry_code_df[industry_code_df == 613301] = 6133
        industry_code_df[industry_code_df == 611902] = 6133
        industry_code_df[industry_code_df == 611903] = 613401
        industry_code_df[industry_code_df == 611904] = 613402
        industry_code_df[industry_code_df == 611901] = 613403
        if not split_fin:
            industry_fin_position = np.logical_or(np.logical_or(industry_code_df == 613401, industry_code_df == 613402), industry_code_df == 613403)
            industry_code_df[industry_fin_position] = 6134
        return industry_code_df

    def LoadValidStocks(self, pool_valid_stocks, trading_pool_dates, all_stocks, prev_portfolio_weight, date, his_dates, is_valid_raw_st, rebalance_times, act_dict):
        date_valid_stocks_all = sorted(set(pool_valid_stocks) - set(['000018.SZ']))
        if trading_pool_dates is not None and trading_pool_dates[0] < date.strftime('%Y%m%d'):
            trading_pool_date = trading_pool_dates[(date.strftime('%Y%m%d') > trading_pool_dates)][(-1)]
            print('trading pool date : ', trading_pool_date)
            trading_pool_stk = pd.read_excel(('/data/user/011477/order/O32/pool/trading_pool_' + trading_pool_date + '.xls'), converters={'证券代码': str})['证券代码']
            trading_pool_stk = [abc + '.SH' if abc[0] == '6' else abc + '.SZ' for abc in trading_pool_stk.values]
            non_pool_stk = sorted(set(all_stocks) - set(trading_pool_stk))
            non_pool_to_sell_stk = sorted(set(prev_portfolio_weight[(prev_portfolio_weight > 0.0)].index.tolist()) & set(non_pool_stk))
            non_pool_invalid_stk = sorted(set(prev_portfolio_weight[(prev_portfolio_weight <= 0.0)].index.tolist()) & set(non_pool_stk))
            date_valid_stocks_all = sorted(set(date_valid_stocks_all) - set(non_pool_invalid_stk))
            for tt in rebalance_times:
                act_dict[tt].loc[(date, non_pool_stk)] = np.nan

        if date in his_dates:
            date_is_valid_raw = is_valid_raw_st.loc[date]
            date_trading_stocks = date_is_valid_raw[(date_is_valid_raw == 1)].index.tolist()
            date_valid_stocks_all = sorted(set(date_valid_stocks_all).intersection(date_trading_stocks))
        return date_valid_stocks_all

    def UpdateDateValidStock(self, date, time, his_dates, prev_date, close, pre_close, st, date_valid_stocks_all):
        if date in his_dates:
            if time == '0930':
                close_ = close.loc[prev_date]
                pre_close_ = pre_close.loc[prev_date]
                st_ = st.loc[prev_date]
            else:
                close_ = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/' + date.strftime('%Y%m%d') + '.pkl').iloc[119]
                pre_close_ = pre_close.loc[date]
                st_ = st.loc[date]
            returns = close_ / pre_close_ - 1.0
            maxup_stk = returns[((returns >= 0.098) | (returns >= 0.048) & (st_ == 1))].index.tolist()
            maxdown_stk = returns[((returns <= -0.098) | (returns <= -0.048) & (st_ == 1))].index.tolist()
            if date.strftime('%Y%m%d') > '20200824' or date.strftime('%Y%m%d') == '20200824' and time not in ('0930', ):
                print('CYB New')
                stk = close.columns.tolist()
                stk_cyb = [i for i in stk if i[0] == '3']
                stk_cyb_max = list(set(stk_cyb) & set(maxup_stk + maxdown_stk))
                if len(stk_cyb_max) != 0:
                    maxup_stk = list(set(maxup_stk) - set(stk_cyb_max))
                    maxdown_stk = list(set(maxdown_stk) - set(stk_cyb_max))
                    stk_cyb_maxup = list(returns.loc[stk_cyb_max][(returns.loc[stk_cyb_max] >= 0.198)].index)
                    maxup_stk.extend(stk_cyb_maxup)
                    stk_cyb_maxdown = list(returns.loc[stk_cyb_max][(returns.loc[stk_cyb_max] <= -0.198)].index)
                    maxdown_stk.extend(stk_cyb_maxdown)
            date_valid_stocks = sorted(set(date_valid_stocks_all) - set(maxup_stk) - set(maxdown_stk))
        else:
            date_valid_stocks = copy.copy(date_valid_stocks_all)
            if time == '0930':
                st_ = st.loc[prev_date]
            else:
                st_ = st.loc[date]
        return (
         date_valid_stocks, st_)

    def optimize_hf(self, act_dict, turnover_adversion_dict, hedge_index='ZZ500', capital=500000000.0, barra_limit_dict={}, industry_loose=0.025, single_stock_max_weight=0.01, amt_limit=0.025, amt_limit_window=5, prev_weights=None, lower_limit=None, pool_valid_stocks=None, dupl_industry=[
 6133, 613401, 613402, 613403], split_fin=True, pools_use=False, test_key=None, simulate_label=True, open_label=False):
        rebalance_times, optimizing_dates = self.LoadRebalanceTime(act_dict)
        index_weights = self.LoadIndexWeight(simulate_label, hedge_index)
        industry_code_df = self.LoadIndustry(split_fin)
        industry_list = sorted(industry_code_df.stack().unique().tolist())
        pre_close, close, vwap_adj, is_valid, is_valid_forward1, is_valid_raw, is_valid_raw_st, st, amt, avg_amt, is_valid_count, is_valid_count_max_prev_5d, barra_factor, index_barra_df, index_industry_total_weight_df = self.LoadPV(amt_limit_window, hedge_index, index_weights, industry_code_df)
        trading_pool_dates = None
        his_dates = close.index.tolist()
        all_stocks = close.columns.tolist()
        if pool_valid_stocks is None:
            pool_valid_stocks = close.columns.tolist()
            trading_pool_dates = np.array(sorted([abc[-12:-4] for abc in os.listdir('/data/user/011477/order/O32/pool/') if abc.find('trading_pool_') == 0]))
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
        prev_portfolio_weight = pd.Series(index=all_stocks, data=(np.array(w0).flatten()))
        dis = 0
        kep_res = pd.DataFrame()
        cell_cnt = 0
        for date in optimizing_dates:
            dis += 1
            start = tm.time()
            if date in his_dates:
                prev_date = his_dates[(his_dates.index(date) - 1)]
            else:
                prev_date = his_dates[(-1)]
                print('should be the very new day to be optimized')
            date_valid_stocks_all = self.LoadValidStocks(pool_valid_stocks, trading_pool_dates, all_stocks, prev_portfolio_weight, date, his_dates, is_valid_raw_st, rebalance_times, act_dict)
            if date not in my_2015_his_dates or is_valid_count[date] / is_valid_count_max_prev_5d[date] >= 0.8 or date == optimizing_dates[0]:
                rebalance = True
            date_avg_amt = avg_amt.loc[prev_date]
            date_index_weight = index_weights.loc[prev_date]
            date_industry_code = industry_code_df.loc[prev_date]
            date_index_indus_weight = index_industry_total_weight_df.loc[prev_date]
            date_index_barra = index_barra_df.loc[prev_date]
            date_barra_factor = barra_factor.loc[prev_date]
            index_stock_wo_industry_code_idx = np.logical_and(date_index_weight > 0, pd.isnull(date_industry_code))
            if index_stock_wo_industry_code_idx.sum() > 0:
                print(date_index_weight.loc[index_stock_wo_industry_code_idx])
                raise AssertionError(str(prev_date) + ' , the above stock in ' + hedge_index + ' has no industry code')
            end = tm.time()
            print('step2 time=' + str(end - start))
            start = tm.time()
            today_buy_portfolio_weight = pd.Series(index=all_stocks, data=lower_w)
            last_time_portfolio_weight = prev_portfolio_weight
            iimp = {}
            for z in range(len(last_time_portfolio_weight)):
                iimp[last_time_portfolio_weight.index[z]] = z

            for time in rebalance_times:
                start = tm.time()
                print(time)
                date_valid_stocks, st_ = self.UpdateDateValidStock(date, time, his_dates, prev_date, close, pre_close, st, date_valid_stocks_all)
                date_valid_stocks_mask = [
                 0] * len(last_time_portfolio_weight)
                for v in date_valid_stocks:
                    date_valid_stocks_mask[iimp[v]] = 1

                st_mask = [0] * len(last_time_portfolio_weight)
                prev_portfolio_weight = self.adjust_excess_index_indus_weight(prev_portfolio_weight, date_industry_code, date_index_indus_weight, date_valid_stocks)
                dupl_industry_weights = {}
                if hedge_index in ('HS300', 'ZZ800'):
                    if dupl_industry is not None:
                        dupl_industry_weights = self.get_dupl_industry_weight(prev_date, dupl_industry, date_valid_stocks, prev_portfolio_weight, date_index_weight, date_industry_code, date_index_indus_weight)
                date_act_series = act_dict[time].loc[date]
                date_act_series = date_act_series.reindex(index=(date_index_weight.index))
                date_act_series[np.isinf(date_act_series)] = np.nan
                single_stock_min_weight_series = today_buy_portfolio_weight.tolist()
                if single_stock_min_weight_series is None or len(single_stock_min_weight_series) == 0:
                    single_stock_min_weight_series = [
                     0] * len(prev_portfolio_weight)
                turnover_adversion_ = turnover_adversion_dict[time]
                if open_label is False:
                    pass
                else:
                    if date == optimizing_dates[0]:
                        open_label = True
                        print('First open_label', open_label)
                    else:
                        open_label = False
                    print('open_label', open_label)
                    end = tm.time()
                    print('before optimize one time=' + str(end - start))
                    start = tm.time()
                    print('valid stock length:' + str(len(date_valid_stocks)))
                    this_time_portfolio_weight = self.get_weights(date, date_act_series, last_time_portfolio_weight,
                      date_valid_stocks,
                      date_valid_stocks_mask,
                      date_avg_amt,
                      capital,
                      (list(date_industry_code)),
                      date_index_indus_weight,
                      (pd.get_dummies(date_industry_code)),
                      date_index_barra,
                      date_barra_factor,
                      barra_limit_dict,
                      industry_loose,
                      turnover_adversion_,
                      single_stock_min_weight_series,
                      single_stock_max_weight,
                      amt_limit,
                      rebalance=rebalance,
                      dupl_industry_weights=dupl_industry_weights,
                      st_=st_,
                      st_mask=st_mask,
                      open_label=open_label)
                    end = tm.time()
                    print('optimize one time=' + str(end - start))
                if this_time_portfolio_weight is None:
                    this_time_portfolio_weight = last_time_portfolio_weight.copy()
                today_buy_portfolio_weight += np.maximum(this_time_portfolio_weight - last_time_portfolio_weight, 0)
                last_time_portfolio_weight = this_time_portfolio_weight
                if time not in multi_date_portfolio_weight:
                    multi_date_portfolio_weight[time] = {}
                multi_date_portfolio_weight[time][date] = this_time_portfolio_weight
                kep_res[date] = this_time_portfolio_weight
                cell_cnt += 1

            prev_portfolio_weight = last_time_portfolio_weight.copy()

        res = {k:pd.DataFrame(v).T for k, v in multi_date_portfolio_weight.items()}
        import pickle
        with open(self.save_path, 'wb') as (f):
            pickle.dump(res, f, pickle.HIGHEST_PROTOCOL)
        return res

    def get_index_barra(self, factor_barra_path, hedge_index, index_weights):
        barra_factor_names = [
         'Beta' + hedge_index[-3:], 'EarningsYield', 'Growth', 'Leverage', 'Liquidity', 'Momentum', 'Size', 'Value', 'Volatility']

        def single(f):
            tmp = pd.read_pickle(factor_barra_path + f + '.pkl')
            return tmp

        barra_dict = {f:single(f) for f in barra_factor_names}
        barra_factor = pd.DataFrame({k:v.stack(dropna=False) for k, v in barra_dict.items()})
        index_barra_df = pd.DataFrame({k:(index_weights * v).sum(axis=1) for k, v in barra_dict.items()})
        return (barra_factor, index_barra_df)

    def get_index_indus_weight(self, index_weights, industry_code_df):
        index_indus = index_weights.stack(dropna=False).to_frame('index_weights')
        index_indus['industry_code_df'] = industry_code_df.stack(dropna=False)
        return index_indus.reset_index().groupby(by=['level_0', 'industry_code_df'])['index_weights'].sum().unstack()

    def adjust_excess_index_indus_weight(self, prev_portfolio_weight, industry_code, index_indus_weight, valid_stocks):
        date_invalid_stocks_in_prev_portfolio = list(set(prev_portfolio_weight[(prev_portfolio_weight > 0)].index) - set(valid_stocks))
        portfolio_weights_industry_code_df = pd.DataFrame(index=['weight', 'industry'], data=[prev_portfolio_weight, industry_code]).T
        portfolio_invalid_stocks_weights_industry_code_df = portfolio_weights_industry_code_df.loc[date_invalid_stocks_in_prev_portfolio]
        portfolio_invalid_stocks_industry_total_weight_series = portfolio_invalid_stocks_weights_industry_code_df.groupby('industry').sum()['weight']
        diff_portfolio_invalid_stocks_index_industry_total_weight = portfolio_invalid_stocks_industry_total_weight_series - index_indus_weight.loc[portfolio_invalid_stocks_industry_total_weight_series.index]
        invalid_excess_index_industry_list = diff_portfolio_invalid_stocks_index_industry_total_weight[(diff_portfolio_invalid_stocks_index_industry_total_weight > 0)].index.tolist()
        if len(invalid_excess_index_industry_list) > 0:
            print('warning: excess index industry weight due to invalid stock weights')
            print(invalid_excess_index_industry_list)
            print()
        for industry in invalid_excess_index_industry_list:
            print(industry)
            invalid_excess_index_industry_stocks = set(prev_portfolio_weight[(industry_code == industry)].index).intersection(date_invalid_stocks_in_prev_portfolio)
            prev_portfolio_weight[invalid_excess_index_industry_stocks] *= index_indus_weight.loc[industry] / portfolio_invalid_stocks_industry_total_weight_series[industry]

        return prev_portfolio_weight

    def get_dupl_industry_weight(self, prev_date, dupl_industry, valid_stocks, portfolio_weight, index_weight, industry_code, index_indus_weight):
        print('adjust duplicate industry stock weight')
        dupl_industry_weight = {}
        for k in dupl_industry:
            index_dupl_industry_stocks_flag = np.logical_and(industry_code == k, index_weight > 0)
            index_dupl_industry_valid_stocks = list(set(index_dupl_industry_stocks_flag[index_dupl_industry_stocks_flag].index.tolist()).intersection(valid_stocks))
            if len(index_dupl_industry_valid_stocks) == 0:
                raise AssertionError(str(prev_date) + ', abnormality: all ' + ' stocks of industry ' + str(k) + ' are invalid')
            portfolio_dupl_industry_stocks_idx = np.logical_and(industry_code == k, portfolio_weight > 0)
            portfolio_dupl_industry_invalid_stocks = list(set(portfolio_weight[portfolio_dupl_industry_stocks_idx].index) - set(valid_stocks))
            portfolio_dupl_industry_invalid_stocks_total_weight = portfolio_weight.loc[portfolio_dupl_industry_invalid_stocks].sum()
            if portfolio_dupl_industry_invalid_stocks_total_weight > index_indus_weight[k]:
                raise AssertionError(str(prev_date) + ', total weight of invalid stock in ' + str(k) + ', ' + str(portfolio_dupl_industry_invalid_stocks_total_weight) + ', exceeds total weight of ' + str(k) + ', ' + str(index_indus_weight))
            adjust_total_weight = index_indus_weight.loc[k] - portfolio_dupl_industry_invalid_stocks_total_weight
            dupl_industry_weight[k] = index_weight.loc[index_dupl_industry_valid_stocks] / index_weight.loc[index_dupl_industry_valid_stocks].sum() * adjust_total_weight
            dupl_industry_weight[k] = dupl_industry_weight[k].round(10)

        assert len(set(dupl_industry_weight.keys()) - set(dupl_industry)) == 0, 'missing adjusted industry weight'
        return dupl_industry_weight

    def get_weights(self, date, date_act_series, prev_portfolio_weight, valid_stocks, valid_stocks_mask, avg_amt, capital, industry_code, index_indus_weight, industry_stock, index_barra, barra_stock, barra_limit_dict, industry_loose, turnover_adversion, single_stock_min_weight_series=None, single_stock_max_weight=0.001, amt_limit=0.025, rebalance=True, dupl_industry_weights={}, st_=None, st_mask=None, open_label=False):
        allstart = tm.time()
        start = tm.time()
        all_stocks = date_act_series.index
        w0 = np.zeros(len(all_stocks))
        if prev_portfolio_weight is not None:
            w0 = prev_portfolio_weight.loc[all_stocks].fillna(0).values
        optimized_weights_list = []
        optimized_stocks_list = []
        w = cvx.Variable((len(all_stocks)), nonneg=True)
        expected_return = date_act_series.fillna(-50).values.astype(np.float64)
        objective = cvx.Maximize(expected_return.T @ w - turnover_adversion * cvx.sum(cvx.elementwise.abs.abs(w - w0)))
        constraints = []
        constraints.append(cvx.sum(w) == 1)
        lower_bound = []
        upper_bound = []
        end = tm.time()
        print('prepare part 0 time = ' + str(end - start) + ' ' + str(end - allstart))
        start = tm.time()
        if st_ is not None:
            st_stk = st_[(st_ == 1)].index.tolist()
        else:
            ii = -1
            mulp5 = amt_limit * 5 / capital
            mulp1 = amt_limit / capital
            for z in range(len(all_stocks)):
                stock = all_stocks[z]
                ii += 1
                start = tm.time()
                if open_label is True:
                    delta = avg_amt[z] * mulp5
                    amt_bound_up = w0[ii] + delta
                    amt_bound_down = w0[ii] - delta
                else:
                    delta = avg_amt[z] * amt_limit / capital
                    amt_bound_up = w0[ii] + delta
                    amt_bound_down = w0[ii] - delta
                up_bound = 0
                up_bound = amt_bound_down if single_stock_min_weight_series[z] < amt_bound_down else single_stock_min_weight_series[z]
                minv = single_stock_max_weight if single_stock_max_weight < amt_bound_up else amt_bound_up
                bound = (up_bound, minv)
                if up_bound > minv:
                    bound = (
                     up_bound, up_bound)
                stock_industry_code = industry_code[z]
                if stock_industry_code in dupl_industry_weights:
                    if stock in dupl_industry_weights[stock_industry_code] and dupl_industry_weights[stock_industry_code].loc[stock] > 1e-05:
                        bound = (
                         dupl_industry_weights[stock_industry_code].loc[stock] - 1e-05,
                         dupl_industry_weights[stock_industry_code].loc[stock] + 1e-05)
                        if up_bound > bound[1]:
                            up_bound = bound[1]
                    else:
                        bound = (0, 0)
                        up_bound = bound[1]
                prevw = prev_portfolio_weight[z]
                if valid_stocks_mask[z] == 0:
                    if prevw > 0:
                        if st_ is None or st_ is not None and stock not in st_stk:
                            bound = (prevw, prevw)
                        else:
                            print(date, stock, 'stock not in st_stk')
                            bound = (0, 0)
                            up_bound = 0
                    else:
                        bound = (0, 0)
                        up_bound = 0
                lower_bound.append(max(bound[0], up_bound))
                upper_bound.append(bound[1])

            constraints.append(w >= lower_bound)
            constraints.append(w <= upper_bound)
            end = tm.time()
            print('prepare part 1 time = ' + str(end - start) + ' ' + str(end - allstart))
            start = tm.time()
            single_up_bound = pd.Series(index=all_stocks, data=upper_bound)
            single_low_bound = pd.Series(index=all_stocks, data=lower_bound)
            index_indus_weight = index_indus_weight[(index_indus_weight != 0)]
            industry_list = sorted(list(set(industry_stock.columns) & set(index_indus_weight.index)))
            for industry in industry_list:
                industry_values = industry_stock[industry].values
                single_indus_stock_max_up = (single_up_bound * industry_values).sum()
                single_indus_stock_min_down = (single_low_bound * industry_values).sum()
                upper_bound = index_indus_weight.loc[industry] * (1 + industry_loose)
                lower_bound = index_indus_weight.loc[industry] * (1 - industry_loose)
                if lower_bound > single_indus_stock_max_up:
                    print(industry, '单股票最大限制:', np.round(single_indus_stock_max_up, 6), '行业最小限制:', np.round(lower_bound, 6))
                    lower_bound = single_indus_stock_max_up
                if upper_bound < single_indus_stock_min_down:
                    print(industry, '单股票最小限制:', np.round(single_indus_stock_min_down, 6), '行业最大限制:', np.round(upper_bound, 6))
                    upper_bound = single_indus_stock_min_down
                constraints.append(industry_values * w >= lower_bound)
                constraints.append(industry_values * w <= upper_bound)

            end = tm.time()
            print('prepare part 2 time = ' + str(end - start))
            for factor in barra_limit_dict.keys():
                barra_values = barra_stock[factor].fillna(0).values
                lower_bound = index_barra.loc[factor] / 1.0 - barra_limit_dict[factor][0]
                upper_bound = index_barra.loc[factor] / 1.0 + barra_limit_dict[factor][1]
                constraints.append(barra_values * w >= lower_bound)
                constraints.append(barra_values * w <= upper_bound)

            start = tm.time()
            prob = cvx.Problem(objective, constraints)
            end = tm.time()
            print('define problem time = ' + str(end - start) + ' ' + str(end - allstart))
            try:
                start = tm.time()
                maximum_activition = prob.solve(verbose=False, solver=(cvx.ECOS), reltol=0.001, warm_start=True)
                end = tm.time()
                print('prob solve time = ' + str(end - start) + ' ' + str(end - allstart))
            except:
                print(date, ' SolverError!!!')
                return
                if maximum_activition == np.inf or maximum_activition == -np.inf:
                    print(date, 'No solution')
                    optimized_weights_list.append([])
                    optimized_stocks_list.append([])
                else:
                    start = tm.time()
                    if rebalance:
                        weight_today = pd.Series((np.array(w.value)), index=all_stocks)
                    else:
                        print(str(date) + ', portfolio weights not rebalanced')
                    print(date, 'select stocks number: ', len(weight_today[(weight_today > 1e-05)]))
                    weight_today[weight_today <= 1e-05] = 0
                    weight_today = weight_today.round(10)
                    optimized_weights_list.append(weight_today.values)
                    optimized_stocks_list.append(weight_today.index)
                    end = tm.time()
                    print('return part time = ' + str(end - start) + ' ' + str(end - allstart))
                return weight_today