import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
try:
    from .normalization_utils import Normalization2
except:
    from normalization_utils import Normalization2

def get_sample_flag(excess, in_sample=True, random_state=0, bootstrap_steps=9, experiment_steps=10):
    assert bootstrap_steps >= 1, "bootstrap_steps must be >= 1"
    ret_diff = []  # record sample excess of each sample process

    for i in range(experiment_steps):
        ret_diff.append(
            sample_random(excess, random_state=random_state, bootstrap_steps=bootstrap_steps) * 1e4)
        random_state += 1
    ret_diff = pd.Series(ret_diff)
    ret_diff_mean = abs(ret_diff.mean())

    if ret_diff_mean == 0:
        return np.inf
    ret_diff_gap = ret_diff.nlargest(experiment_steps // 2).mean() - ret_diff.nsmallest(
        experiment_steps // 2).mean()
    ret_diff_value = ret_diff_gap / ret_diff_mean
    return ret_diff_value
        
        
def sample_random(excess, random_state, bootstrap_steps):
    sample_10, sample_90 = train_test_split(excess, test_size=1 - 1 / (bootstrap_steps + 1),
                                            random_state=random_state)
    # part 2:bootstrap sampling of the rest 90%
    excess_sample = sample_10.to_list()
    for i in range(bootstrap_steps):
        sample_new = sample_90.sample(n=len(sample_10), replace=True, random_state=random_state).to_list()
        excess_sample += sample_new
        random_state += 10
    return pd.Series(excess_sample).mean()



# def gplearn_offical_alpha(y, y_pred, w, decap_df, data_index):
#     # def get_residual(series):
#     #     reg_list = [ 'norm_size','code_6101','code_6102','code_6103','code_6104','code_6105',
#     #                  'code_6108','code_6111','code_6112','code_6113','code_6114','code_6115',
#     #                  'code_6116','code_6117','code_6118','code_6120','code_6121',
#     #                  'code_6123','code_6124','code_6125','code_6126',
#     #                  'code_6127','code_6128','code_6129','code_6130',
#     #                  'code_6131','code_6132','code_6133','code_6134']             
#     #     factor_series = pd.Series(np.nan, index=series.index)
#     #     prepared_neu = series.dropna()    
#     #     Y = prepared_neu[['y_pred']].values
#     #     X = prepared_neu[reg_list].values
#     #     if len(prepared_neu) >= 100: 
#     #         reg = LinearRegression(fit_intercept=False, n_jobs=1)
#     #         reg.fit(X, Y)
#     #         res = Y - reg.predict(X)
#     #         y_pred = res.reshape(-1)
#     #     else:
#     #         y_pred = Y.reshape(-1)
#     #     factor_series.loc[prepared_neu.index] = y_pred
#     #     return factor_series

#     assert len(data_index) == len(y_pred)
#     assert len(data_index) == len(y)

#     # 配置
#     top_range = 0.1
#     turnover_rate = 0
#     rho = 0.0004
#     # # 合并真实标签
#     # tt = pd.DataFrame(y_pred, columns=['y_pred_raw'], index=data_index)
#     # tt['1Day_return'] = y
#     # # 用left方法合并，decap_file
#     # tt = tt.merge(decap_df, how='left', left_index=True, right_index=True) 
#     # # print("================ len tt =============={}".format(len(tt)))
#     # is_invalid = (tt['valid'] == False)
#     # # 把invalid的地方，对应的return和factor的值都置为np.nan
#     # tt.loc[is_invalid, "y_pred_raw"] = np.nan
#     # tt.loc[is_invalid, "1Day_return"] = np.nan
#     # 计算de-mean收益
#     re_1d = tt['1Day_return'].unstack()
#     excess_return = re_1d.subtract(re_1d.mean(axis=1), axis=0)

    
#     valid_tt = tt[tt['valid'] ==True]
#     final_samples_num = len(valid_tt)
    
#     # 标准化因子, 获得残差
#     # tt['y_pred'] = tt['y_pred_raw'].replace([-np.inf, np.inf], np.nan) #这一步可以不做，因为在normalization中有
#     # tmp = tt[['y_pred']].unstack()
#     # normalizer = Normalization2(axis=0)
#     # factor_df = normalizer.norm_dataframe(tmp)
#     # normalized_factor_df = factor_df.stack()
#     tt['y_pred'] = normalized_factor_df['y_pred']
#     tt['res'] = tt.groupby("mddate").apply(get_residual).droplevel(0)

#     # 计算组合的超额收益
#     factor_df = tt['res'].unstack()
#     ## 排序
#     factor_ranker_pct_descending = factor_df.rank(pct=True, axis=1, method='first', ascending=False)
#     wi_descending_01 = ((factor_ranker_pct_descending <= top_range) * 1).fillna(0)
#     ## 计算换手率
#     wi_descending = factor_ranker_pct_descending.fillna(0) * wi_descending_01
#     wi_descending = wi_descending_01
#     ## 这里是为什么除以2呢？答：调入计0.5， 调出计0.5，一轮总和为1，平摊手续费
#     wi_turnover = (wi_descending - wi_descending.shift(1)).applymap(abs) / 2
#     ## 每天换出去的股票/ 总的被选中的股票数
#     turnover_rate = wi_turnover.sum(axis=1) / wi_descending.sum(axis=1)
#     turnover_rate[np.isinf(turnover_rate)] = np.nan
#     ## 计算平均数
#     wi_descending = wi_descending.divide(wi_descending.sum(axis=1), axis=0)
#     excess_descending = ((wi_descending * excess_return).sum(axis=1))
#     excess_descending = excess_descending - rho * turnover_rate

#     original_day = len(excess_descending)
#     excess_descending = excess_descending.dropna()
#     nan_ratio = len(excess_descending) / original_day
#     average_excess_return = excess_descending.mean()

#     return average_excess_return, nan_ratio, final_samples_num

def gplearn_offical_alpha(df, column_name="y_pred_resi", mode="avg"):
    # 配置
    top_range = 0.1
    turnover_rate = 0
    rho = 0.0004
    re_1d = df['1Day_return'].unstack()
    excess_return = re_1d.subtract(re_1d.mean(axis=1), axis=0)

    valid_tt = df[df['valid'] ==True]
    final_samples_num = len(valid_tt)

    # 计算组合的超额收益
    factor_df = df[column_name].unstack()
    ## 排序
    factor_ranker_pct_descending = factor_df.rank(pct=True, axis=1, method='first', ascending=False)
    wi_descending_01 = ((factor_ranker_pct_descending <= top_range) * 1).fillna(0)
    ## 计算换手率
    wi_descending = factor_ranker_pct_descending.fillna(0) * wi_descending_01
    wi_descending = wi_descending_01
    ## 这里是为什么除以2呢？答：调入计0.5， 调出计0.5，一轮总和为1，平摊手续费
    wi_turnover = (wi_descending - wi_descending.shift(1)).applymap(abs) / 2
    ## 每天换出去的股票/ 总的被选中的股票数
    turnover_rate = wi_turnover.sum(axis=1) / wi_descending.sum(axis=1)
    turnover_rate[np.isinf(turnover_rate)] = np.nan
    ## 计算平均数
    wi_descending = wi_descending.divide(wi_descending.sum(axis=1), axis=0)
    excess_descending = ((wi_descending * excess_return).sum(axis=1))
    excess_descending = excess_descending - rho * turnover_rate

    original_day = len(excess_descending)
    excess_descending = excess_descending.dropna()
    nan_ratio = len(excess_descending) / original_day
    average_excess_return = excess_descending.mean()

    if mode == "avg":
        return average_excess_return, nan_ratio, final_samples_num
    else:
        return excess_descending, nan_ratio, final_samples_num


def gplearn_offical_alpha_seq(y, y_pred, w, decap_df, data_index):
    def get_residual(series):
        reg_list = [ 'norm_size','code_6101','code_6102','code_6103','code_6104','code_6105',
                     'code_6108','code_6111','code_6112','code_6113','code_6114','code_6115',
                     'code_6116','code_6117','code_6118','code_6120','code_6121',
                     'code_6123','code_6124','code_6125','code_6126',
                     'code_6127','code_6128','code_6129','code_6130',
                     'code_6131','code_6132','code_6133','code_6134']             
        y_true = series['excess_return'].values
        Y = series[['y_pred']].values
        X = series[reg_list].values
        if len(series) >= 1000: 
            reg = LinearRegression(fit_intercept=False, n_jobs=1)
            reg.fit(X, Y)
            res = Y - reg.predict(X)
            y_pred = res.reshape(-1)
        else:
            y_pred = Y
        top_portfolio = np.argsort(y_pred)[::-1][:max(int(len(series) * 0.1), 1)]
        alpha = np.mean(y_true[top_portfolio])
        #TODO 如果不能分10层，返回一个较大值
        ans = {}
        ans['top_10_alpha'] = alpha
        return pd.Series(ans)

    # 选择股票池
    # multi_index = decap_df.index #-> 最终需要的index

    assert len(data_index) == len(y_pred)
    assert len(data_index) == len(y)

    # 数据
    tt = pd.DataFrame(y_pred, columns=['y_pred_raw'], index=data_index)
    tt['1Day_return'] = y


    tt = tt.merge(decap_df, how='inner', left_index=True, right_index=True)
    tt = tt[ tt['valid'] ==True ] # 这一步要去掉
    valid_index = tt.index 
    
    # 标准化因子
    tt['y_pred'] = tt['y_pred_raw'].replace([-np.inf, np.inf], np.nan)

    tmp = tt[['y_pred']].unstack()
    normalizer = Normalization2(axis=0)
    factor_df = normalizer.norm_dataframe(tmp)
    normalized_factor_df = factor_df.stack()
    normalized_factor_df = normalized_factor_df.loc[valid_index]
    tt['y_pred'] = normalized_factor_df['y_pred']
    tt['y_pred'] = tt['y_pred'].groupby("mddate").transform(lambda x: x.fillna(x.mean()))
    # 获得超额收益序列
    tt['excess_return'] = tt['1Day_return'] - tt.groupby("mddate")['1Day_return'].transform("mean")
    tt.dropna(how='any', axis=0, inplace=True)
    ans = tt.groupby("mddate").apply(get_residual)
    return ans