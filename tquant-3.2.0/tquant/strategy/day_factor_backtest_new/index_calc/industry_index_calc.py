import numpy as np


def calc_hhi(factor_pd, positive_only=True):
    """
    建产业集中度，
    :param factor_pd: 行为日期，列为行业
    :param positive_only:
    :return:
    """
    pos_mask = factor_pd > 0
    if positive_only:
        fac = factor_pd[pos_mask].copy()
    else:
        fac = factor_pd.copy()
    fac_pct = fac.divide(fac.sum(axis=1), axis=0)
    use_mask = np.isfinite(fac_pct).sum(axis=1) > 0
    fac_hhi = ((fac_pct * 100) ** 2).sum(axis=1) / 100 ** 2
    fac_hhi[~use_mask] = np.nan
    fac_hhi.index.name = 'industry concentration'
    return fac_hhi
