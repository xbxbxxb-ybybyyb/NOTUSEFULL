import pandas as pd
import numpy as np
import scipy.stats as sps
from collections import OrderedDict

from tquant.strategy.day_factor_backtest_new.data.data_preprocess import regression_ols
from tquant.strategy.day_factor_backtest_new.index_calc.evaluative_index_calc import calc_factor_ic


def regression_analysis(standardized_data, neutral_dict_df, holding_period_ret, ic_type='original'):
    """
    VIF = 1 / (1-R2)
    0 < VIF < 10, no collinearity；10 ≤ VIF < 100, middle state, VIF ≥ 100, strong collinearity
    OLS 1: F(factor_to_be_test) = F(Style) * Beta(Style) + X(Industry) * Beta(Industry) + Resid
    OLS 2: R(stock_return) = Resid * Beta(Resid) + ~Resid
    output: ols2.tstat, ols2.beta, VIF, IC
    """
    # 用neutral_list中的数据做了回归预测
    neutralized_data, r2, _, _ = regression_ols(standardized_data, neutral_dict_df)
    _, _, beta, tstats = regression_ols(holding_period_ret, {'resid': neutralized_data})
    r2 = pd.DataFrame(r2)
    vif = 1 / (1 - r2[r2 < 1])
    IC = calc_factor_ic(neutralized_data, holding_period_ret, ic_type=ic_type)
    output_pd = pd.concat([tstats[['resid']], beta[['resid']], r2, vif, IC], axis=1)
    output_pd.columns = ['T-stat', 'Beta', 'Rsq', 'VIF', 'IC']
    return output_pd


def regression_stats_process(output_pd, neutral_list=[], name=None):
    ttest, factor_beta, rsq, vif, IC = output_pd['T-stat'], output_pd['Beta'], output_pd['Rsq'], output_pd['VIF'], \
                                       output_pd['IC']
    ttest_avg = ttest.mean()
    ttest_abs_avg = ttest.abs().mean()
    ttestg2pct = (ttest > 2).sum() / len(ttest) if len(ttest) > 0 else np.nan
    ttest_sharpe = ttest_avg / ttest.std() if ttest.std() != 0 else np.nan
    factor_beta_mean = factor_beta.mean()
    factor_beta_t = sps.ttest_1samp(factor_beta.dropna(), popmean=0).statistic
    IC_avg = IC.mean()
    IC_std = IC.std()
    IR = IC_avg / IC_std if IC_std != 0 else np.nan
    IC_pos = (IC > 0).sum() / len(IC) if len(IC) != 0 else np.nan
    IC_absg5bp = (IC.abs() > 0.05).sum() / len(IC) if len(IC) != 0 else np.nan
    vif_avg = vif.mean()
    rsq_avg = rsq.mean()
    reg_dict = OrderedDict([
        ('| T-stat | avg', ttest_abs_avg),
        ('T-stat > 2 in %', ttestg2pct),
        ('T-stat (avg / std)', ttest_sharpe),
        ('Beta', factor_beta_mean),
        ('Beta T-Value', factor_beta_t),
        ('IC avg', IC_avg),
        ('IC std', IC_std),
        ('ICIR', IR),
        ('IC > 0 in %', IC_pos),
        ('| IC | > 0.05 in %', IC_absg5bp),
        ('VIF', vif_avg),
        ('R2 (Explained by %s)' % ' , '.join(list(set(neutral_list + ['Industry']))), rsq_avg)])

    regstat = pd.DataFrame(reg_dict, index=[name]).T
    return regstat


