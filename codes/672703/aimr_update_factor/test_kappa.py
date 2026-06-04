import numpy as np
import pandas as pd
import os 
def confusion_matrix(rater_a, rater_b, min_rating=None, max_rating=None):
    assert(len(rater_a) == len(rater_b))
    if min_rating is None:
        min_rating = min(rater_a + rater_b)
    if max_rating is None:
        max_rating = max(rater_a + rater_b)
    num_ratings = int(max_rating - min_rating + 1)
    conf_mat = [[0 for i in range(num_ratings)]
                for j in range(num_ratings)]
    for a, b in zip(rater_a, rater_b):
        conf_mat[a - min_rating][b - min_rating] += 1
    return conf_mat

def histogram(ratings, min_rating=None, max_rating=None):

    if min_rating is None:
        min_rating = min(ratings)
    if max_rating is None:
        max_rating = max(ratings)
    num_ratings = int(max_rating - min_rating + 1)
    hist_ratings = [0 for x in range(num_ratings)]
    for r in ratings:
        hist_ratings[r - min_rating] += 1
    return hist_ratings

def quadratic_weighted_kappa(rater_a, rater_b, min_rating=None, max_rating=None):
    rater_a = np.array(rater_a, dtype=int)
    rater_b = np.array(rater_b, dtype=int)
    assert(len(rater_a) == len(rater_b))
    if min_rating is None:
        min_rating = min(min(rater_a), min(rater_b))
    if max_rating is None:
        max_rating = max(max(rater_a), max(rater_b))
    conf_mat = confusion_matrix(rater_a, rater_b,
                                min_rating, max_rating)
    num_ratings = len(conf_mat)
    num_scored_items = float(len(rater_a))

    hist_rater_a = histogram(rater_a, min_rating, max_rating)
    hist_rater_b = histogram(rater_b, min_rating, max_rating)

    numerator = 0.0
    denominator = 0.0

    for i in range(num_ratings):
        for j in range(num_ratings):
            expected_count = (hist_rater_a[i] * hist_rater_b[j]
                              / num_scored_items)
            d = pow(i - j, 2.0) / pow(num_ratings - 1, 2.0)
            numerator += d * conf_mat[i][j] / num_scored_items
            denominator += d * expected_count / num_scored_items

    return 1.0 - numerator / denominator

def get_clf_kappa_score(pred, labels, cdf, is_cut_off=False):
    num = pred.shape[0]
    pred_score = np.asarray([cdf.shape[0] - 1]*num, dtype=int)
    rank = pred.argsort()
    for index in range(cdf.shape[0] - 1):
        if index == 0:
            pred_score[rank[:int(num*cdf[index]-1)]] = index
        else:
            pred_score[rank[int(num*cdf[index]):int(num*cdf[index + 1]-1)]] = index

    kappa = quadratic_weighted_kappa(pred_score, labels.reshape(-1).astype(np.int32))    

    if is_cut_off:
        cutoff = [pred[rank[int(num*cdf[i]-1)]] for i in range(cdf.shape[0] - 1) ]
        return kappa, cutoff

    return kappa
def get_cdf_rank(num):
    cdf = []
    for i in range(1, num + 1):
        cdf.append(i * 1.0 / num)
    return np.array(cdf)
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
cdf = get_cdf_rank(20)
from sklearn.externals.joblib import Parallel,delayed
def single(date):
    sample = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/NormSample/'+date+'.pkl')
    df_label = sample[label].rank(pct=True)
    df_label = pd.cut(df_label,bins=np.linspace(0,1,20+1),labels=np.arange(1,20+1,1)).astype(np.int64).values
    res = sample[factor_list].apply(lambda x:get_clf_kappa_score(x, df_label, cdf),axis=0)
    return res
path = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'
date_list = sorted([f[:-4] for f in os.listdir(path)])
for i in [1,3,5]:
    label = 'vwap_re_'+str(i)+'d'
    res = Parallel(20)(delayed(single)(date) for date in date_list)
    res = dict(zip(date_list,res))
    f = pd.DataFrame(res).T.sort_index()
    
    f.to_pickle('/data/user/013546/rubbish/kappa'+label+'.pkl')