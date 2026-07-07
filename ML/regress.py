#from __future__ import division import math
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score
#pd.set_option('display.max_rows', None)
import sys

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error,r2_score
from sklearn.preprocessing import MinMaxScaler
 






#b = pd.read_csv("am_filter.csv", index_col=0)
#c = pd.read_csv("an_filter.csv", index_col=0)
#d = pd.read_csv("ao_filter.csv", index_col=0)
#e = pd.read_csv("ap_filter.csv", index_col=0)
#f = pd.read_csv("aq_filter.csv", index_col=0)
#f = pd.read_csv("adjust.csv", index_col=0)
#g = pd.read_csv("origin2016.csv", index_col=0)
#g = pd.read_csv("../../origin2023_vwap.csv", index_col=0)
#g = pd.read_csv("/dfs/user/012316/BTC/MAKDER/ETHUSDT/20250104_TMP/tmp.csv.target", index_col=0)
#g = pd.read_csv("/dfs/user/012316/BTC/MAKDER/ETHUSDT/20250101_TMP/tmp.csv.target", index_col=0)
#g = pd.read_csv("/tmp/20241029_eth.csv.target", index_col=0)
#g = pd.read_csv("/tmp/20250118.csv.target", index_col=0)
#g = pd.read_csv("/dfs/user/012316/BTC/MAKDER/ETHUSDT/20250114_BOOK_5MIN_FACTOR_AGGBINARY.TRAIN_ADJ.csv.target", index_col=0)
#g = pd.read_csv("/dfs/user/012316/BTC/MAKDER/ETHUSDT/20250115_TRADE_5MIN_FACTOR_AGGBINARY.TRAIN_ADJ.csv.target", index_col=0)
#g = pd.read_csv("/dfs/user/022472/SHARE/weipan/label_temp/target/target_buy_vwap_5min_sell_930_vwap_30min.csv", index_col=0)
#g = pd.read_csv("BNBtrain.csv", index_col=0)
#g = pd.read_csv("train.csv", index_col=0)
#g = pd.read_csv(sys.argv[1], index_col=0)
#g = pd.read_csv("/tmp/20250115_TRADE_5MIN_FACTOR_AGGBINARY.TRAIN.csv.target", index_col=0)
#b = pd.read_csv('/dfs/user/012316/BTC/MAKDER/ETHUSDT/20250114_BOOK_5MIN_FACTOR_AGGBINARY.target32000', header=None, index_col=0)
#g['target'] = b[1]
#print(g)
#exit(0)


#a = pd.read_pickle('train_feature.pkl')
a = pd.read_pickle('/home/yzhan/playground/TMPDATA_TRADEAGG/process_l2/1MIN_BAR_2021/train.pkl')
##a = a.iloc[1000000:, :]
#a = a.iloc[990000:1990000, :]
#a = pd.read_csv('/home/yzhan/playground/TMPDATA_TRADEAGG/process_l2/1MIN_BAR_2021/train.csv', index_col=0)

a = a[(a['target'] >= -0.3) & (a['target'] <= 0.3)]
aa = a.copy()
a = (a - a.rolling(20000).mean()) / (a.rolling(20000).std() + 1e-5)
#a = (a - a.rolling(10000).mean()) / a.rolling(10000).std()
a['target'] = aa['target']

print(a)
print(a.corrwith(a['target']))
#exit(0)
del a['open']
del a['p50_open']
del a['p90_open']
del a['open_rolling']
del a['p50_open_rolling']
del a['p90_open_rolling']

del a['close']
del a['p50_close']
del a['p90_close']
del a['close_rolling']
del a['p50_close_rolling']
del a['p90_close_rolling']


del a['high']
del a['p50_high']
del a['p90_high']
del a['high_rolling']
del a['p50_high_rolling']
del a['p90_high_rolling']


del a['low']
del a['p50_low']
del a['p90_low']
del a['low_rolling']
del a['p50_low_rolling']
del a['p90_low_rolling']


del a['volume']
del a['p50_volume']
del a['p90_volume']
del a['volume_rolling']
del a['p50_volume_rolling']
del a['p90_volume_rolling']


#g = pd.read_csv('/data/user/012316/DATA/SHARE_FACTOR_GENERAL/20231023_withlabel_adj.csv', index_col=0)
#g = pd.read_csv('/data/user/012316/OPTIVER/PROD_20231025/OUT_withlabel.csv', index_col=0)
#gm = g.rolling(window=10000, min_periods=1).mean()
#gm = g.copy()
#for cc in gm.columns:
#  gm[cc] = gm[cc].rolling(window=10000, min_periods=1).mean()
#print(gm)
#g = g - gm
#exit(0)

#g = pd.read_csv("cs_raw.csv", index_col=0)
#
#a = g
#print(a)
#a = pd.DataFrame()
#for cc in b.columns:a[cc] = b[cc]
#for cc in c.columns:a[cc] = c[cc]
#for cc in d.columns:a[cc] = d[cc]
#for cc in e.columns:a[cc] = e[cc]
#for cc in f.columns:a[cc] = f[cc]
#for cc in g.columns:a[cc] = g[cc]


#a = pd.concat([a, b, c, d, e], axis=1)
#print(a)
#input()
#a = pd.read_csv("/arch1/user/012316/STRONG_RELATED/DATAS/M1_D0/MINING_MERGE/am.csv", index_col=0)

if ('target' not in a.columns):
  tg = pd.read_csv('m1target.csv', index_col=0, header=None)
  tg = tg.reindex(a.index)
  a['target'] = tg


#am = a.rolling(1000).mean()
#am_std = a.rolling(1000).std()
#y = a['target'].copy()
#a_bak = a
#a['target'] = (a['target'] - am['target']) / am_std['target']
#a = (a - am) / am_std
a = a.replace(np.inf, np.nan)
a = a.replace(-np.inf, np.nan)
a = a.replace(-np.nan, np.nan)
a = a.fillna(0)
#a_bak['target'] = y
#a['target'] = y
#a_bak = a

#a = a[['factor_yzhan_hf_a_40_34','factor_yzhan_hf_a_172_20','factor_yzhan_hf_a_102_14','factor_yzhan_hf_a_109_20','factor_yzhan_hf_a_111_4','factor_yzhan_hf_a_158_4','factor_yzhan_hf_a_149_4','factor_yzhan_hf_a_110_56','factor_yzhan_hf_a_129_54','factor_yzhan_hf_a_111_34','factor_yzhan_hf_a_101_4','factor_yzhan_hf_a_111_42','factor_yzhan_hf_a_110_42','factor_yzhan_hf_a_109_56','factor_yzhan_hf_a_158_42','factor_yzhan_hf_a_63_56','factor_yzhan_hf_a_64_56','factor_yzhan_hf_a_111_56','factor_yzhan_hf_a_111_54','target']]
#
#



##a = pd.read_csv("morepy2.csv", index_col=0)
#a = pd.read_csv("FILTERNEW_filter2.csv", index_col=0)
##a = pd.read_csv("origin.csv", index_col=0)
#
#if ('target' not in a.columns):
#  tg = pd.read_csv('m1target.csv', index_col=0, header=None)
#  tg = tg.reindex(a.index)
#  a['target'] = tg
#
#a = a[['factor_t_l1_norise_num_bda','factor_t_l1_act_bid_rate','factor_wwd_lzt_up_half_act_sell_pct','factor_sundc_t_tran_4','factor_t_l1_bda_up_med','factor_sundc_t_tran_40','factor_t_big_vwap_chg_sdl','factor_sundc_t_tran_37','factor_t_new_ask_rate_sdl','factor_t_each_bid_vol_1d5','factor_t_l5_old_ask_frate','target']]







#a = a.iloc[40000:,:]





#a['target'] = a['target'].rank(pct=True) - 0.5





##a = pd.read_csv('training_small.csv', header=None)
#if (len(sys.argv) > 1):
#  a = pd.read_csv(sys.argv[1], index_col=0)
#else:
#  a = pd.read_csv('origin2016_adj.csv', index_col=0)
#  #a = pd.read_csv('origin2016.csv', index_col=0)
##a = pd.read_csv('morepytg.csv', index_col=0)
##a = a.iloc[35000:,:]
a = a.dropna(how='all', axis=0)
a = a.replace(-np.inf, np.nan)
a = a.replace(np.inf, np.nan)
a = a.replace(-np.nan, np.nan)
a = a.fillna(0)

#a_bak = a_bak.dropna(how='all', axis=0)
#a_bak = a_bak.replace(-np.inf, np.nan)
#a_bak = a_bak.replace(np.inf, np.nan)
#a_bak = a_bak.replace(-np.nan, np.nan)
#a_bak = a_bak.fillna(0)

#a.to_csv('/tmp/debug.csv')
#exit(0)

#print(a)
#exit(0)
#a = a.iloc[:60000,:]

#print(a.shape)
#input()
train_target = a.iloc[:,-1]
print(train_target.shape)
#exit(0)
#train_target_bak = a_bak.iloc[:,-1]

#train_target = train_target - train_target.mean()
#print(train_target)
fsz = a.shape[1] - 1
#input()
maxc = 0

sz = a.shape[0] // 100 * 70
#print(a.iloc[sz])
#input()

for i in range(fsz):
    a.iloc[:,i] = a.iloc[:,i].rank()
    maxv = a.iloc[:,i].max()
    minv = a.iloc[:,i].min()
    #print('min-max ' + str(i) + ' ' + str(minv) + ' ' + str(maxv))
    a.iloc[:,i] = (a.iloc[:,i] - minv) / (maxv - minv) - 0.5
    #if (a.iloc[:sz,i].std() > 0):
    #  a.iloc[:,i] = (a.iloc[:,i] - a.iloc[:sz,i].mean()) / a.iloc[:sz,i].std()
    if (a.iloc[:,i].corr(train_target) > maxc):
      maxc = a.iloc[:,i].corr(train_target)
    #print(a.iloc[:,i].corr(train_target))

a = a.replace(-np.inf, np.nan)
a = a.replace(np.inf, np.nan)
a = a.replace(-np.nan, np.nan)
a = a.fillna(0)



train_data = a.iloc[:,:fsz]


#dim=50
#from sklearn.decomposition import KernelPCA
#kpca = KernelPCA(kernel='rbf', gamma=100,n_components=dim)
##kpca = KernelPCA(kernel='sigmoid', n_components=dim)
#newv = kpca.fit_transform(train_data.values)
#pb = pd.DataFrame(newv)
#print(pb)
##exit(0)
#
#
##for i in range(dim):
##    pb.iloc[:,i] = pb.iloc[:,i].rank() / pb.shape[0]
##print(pb)
##exit(0)
train_data = train_data.values
#train_data = pb.values
#print(train_data)
#print(train_target)
#train_target.to_csv('/tmp/debug.csv')
#exit(0)




#from sklearn.model_selection import train_test_split
#train_X,test_X,train_y,test_y = train_test_split(train_data,train_target,test_size=0.3,random_state=1)
print('db---------------')
print(train_target.shape)
print(train_target.dtype)

train_X = train_data[:sz, :]
train_y = a.iloc[:sz,-1].values#train_target[:sz]
test_X = train_data[sz:, :]
test_y = a.iloc[sz:,-1].values#train_target[sz:]

all_X = train_data[:, :]
all_y = train_target[:]

print('train_data test shape = ')
print(train_X.shape)
print(test_X.shape)


maxc = 0

for i in range(fsz):
    c = np.corrcoef(test_X[:, i], test_y)[0][1]
    if (c > maxc):
      maxc = c
print('maxcorr=' + str(maxc))


#print(train_X)
#print(test_X)

from sklearn.model_selection import GridSearchCV, RepeatedKFold

def svm_c(x_train, x_test, y_train, y_test):
    from sklearn.svm import SVC
    svc = SVC(kernel='rbf')
    c_range = np.logspace(-5, 15, 11, base=2)
    gamma_range = np.logspace(-9, 3, 13, base=2)
    param_grid = [{'kernel':['rbf'], 'C':c_range, 'gamma':gamma_range}]
    grid = GridSearchCV(estimator=svc, param_grid=param_grid)
    clf = grid.fit(x_train, y_train)
    score = grid.score(x_test, y_test)
    print("score=" + str(score))

def svm_c_one(x_train, x_test, y_train, y_test):
    from sklearn.svm import SVC
    #svc = SVC(kernel='rbf', gamma=0.0001, C=1000000)
    svc = SVC(C=10000)
    svc.fit(x_train, y_train)
    py = svc.predict(x_test)
    up = 0
    for i in range(y_test.shape[0]):
        if (py[i] == y_test[i]): up += 1
    print("score=" + str(up / y_test.shape[0]) + " size" + str(y_test.shape[0]))

def reg(x_train, x_test, y_train, y_test):
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model = model.fit(x_train, y_train)
    r_sq = model.score(x_train, y_train)
    #print(r_sq)

    py = model.predict(x_test)
    train_py = model.predict(x_train)

    res = pd.DataFrame({'sig':list(py), 'target':list(y_test)})
    res.to_csv('/tmp/tmp3.csv')

    print('train regresion corr =' + str(np.corrcoef(y_train, train_py)[0][1]))
    print('test regresion corr =' + str(np.corrcoef(y_test, py)[0][1]))
    print('r2 = ' + str(r2_score(y_test, py)))

    b = pd.DataFrame({'col':list(a.columns[:-1]), 'coef':list(model.coef_)})
    b['acoef'] = b['coef'].abs()
    b = b.sort_values(by='acoef', ascending=False)
    print(b)

    mae = mean_absolute_error(y_test, py)
    print('mae=' + str(mae))

def lasso(x_train, x_test, y_train, y_test, all_x, all_y, index):
    from sklearn.linear_model import Lasso
    alpha = 10
    lasso = Lasso(alpha=alpha)
    model = lasso.fit(x_train, y_train)
    py = model.predict(x_test)
    all_py = model.predict(all_x)

    print('corr(test)=' + str(np.corrcoef(y_test, py)[0][1]))
    print('corr(all)=' + str(np.corrcoef(all_y, all_py)[0][1]))
    print('r2 = ' + str(r2_score(y_test, py)))
    all_py = pd.Series(data = all_py, index=index)
    all_py.to_csv('/tmp/all_py.csv')
    
    b = pd.DataFrame({'col':list(a.columns[:-1]), 'coef':list(lasso.coef_)})
    b['acoef'] = b['coef'].abs()
    b = b.sort_values(by='acoef', ascending=False)
    print(b)

def enet(x_train, x_test, y_train, y_test):
    from sklearn.linear_model import ElasticNet
    #enet = ElasticNet(alpha=0.00001, l1_ratio=0.7)
    enet = ElasticNet(alpha=0.0000001, l1_ratio=0.7)

    model = enet.fit(x_train, y_train)
    py = model.predict(x_test)
    #py = model.predict(x_test)
    print('corr =' + str(np.corrcoef(y_test, py)[0][1]))
    print('r2 = ' + str(r2_score(y_test, py)))

def ridge(x_train, x_test, y_train, y_test):
    from sklearn.linear_model import Ridge 
    RR = Ridge(alpha=0.1)
    model = RR .fit(x_train, y_train)
    py = model.predict(x_test)
    #py = model.predict(x_test)
    print('corr =' + str(np.corrcoef(y_test, py)[0][1]))
    print('r2 = ' + str(r2_score(y_test, py)))
def svr(x_train, x_test, y_train, y_test):
    from sklearn.svm import SVR
    #svc = SVC(kernel='rbf', gamma=0.0001, C=1000000)
    #svc = SVR(kernel='linear', gamma=0.1, C=1)
    svc = SVR(kernel='rbf', C=1e3, epsilon=.1)
    yy = pd.DataFrame(y_train)
    xx = pd.DataFrame(x_train)
    print(xx.describe())
    print(yy.describe())

    mm1 = MinMaxScaler()   # 特征进行归一化
    x_train = mm1.fit_transform(x_train)
    x_test = mm1.fit_transform(x_test)

    svc.fit(x_train, y_train)

    #print(y_train)
    py = svc.predict(x_test)
    tt = pd.DataFrame({'a':py, 'b':y_test})
    #print(svc.coef_)
    #print(tt)

    print('corr =' + str(np.corrcoef(y_test, py)[0][1]))
    print('r2 = ' + str(r2_score(y_test, py)))

def knn(x_train, x_test, y_train, y_test):
    from sklearn.neighbors import KNeighborsClassifier
    svc = KNeighborsRegressor(n_neighbors=1)
    svc.fit(x_train, y_train)
    py = svc.predict(x_test)
    up = 0
    down = 0
    m = np.mean(y_test)
    for i in range(y_test.shape[0]):
        up += (py[i] - y_test.iloc[i]) * (py[i] - y_test.iloc[i])
        down += (y_test.iloc[i] - m) * (y_test.iloc[i] - m)
    print("score=" + str(1 - up / down) + " size" + str(y_test.shape[0]))
def RF(x_train, x_test, y_train, y_test):
    from sklearn.ensemble import RandomForestClassifier
    #classifier = RandomForestClassifier(n_estimators = 1000, max_depth=8, min_samples_leaf=1, criterion = 'entropy', random_state = 0)
    #classifier.fit(x_train, y_train)
    #py = classifier.predict(x_test)

    from sklearn.ensemble import RandomForestRegressor
    rgm = RandomForestRegressor(n_estimators=100, max_depth=4, verbose=1, n_jobs=40)
    rgm.fit(x_train, y_train)
    py = rgm.predict(x_test)

    res = pd.DataFrame({'sig':list(py), 'target':list(y_test)})
    res.to_csv('/tmp/rg.csv')

    print('corr =' + str(np.corrcoef(y_test, py)[0][1]))
    print('r2 = ' + str(r2_score(y_test, py)))
   
    train_py = rgm.predict(x_train)

    #res = pd.DataFrame({'sig':list(py), 'target':list(y_test)})
    #res.to_csv('/tmp/tmp3.csv')

    print('train regresion corr =' + str(np.corrcoef(y_train, train_py)[0][1]))
    #print('test regresion corr =' + str(np.corrcoef(y_test, py)[0][1]))


#class FM(Layer):
#    def __init__(self, output_dim=30, activation="relu",**kwargs):
#        self.output_dim = output_dim
#        self.activate = activations.get(activation)
#        super(FM, self).__init__(**kwargs)
#
#    def build(self, input_shape):
#        self.wight = self.add_weight(name='wight', 
#                                      shape=(input_shape[1], self.output_dim),
#                                      initializer='glorot_uniform',
#                                      trainable=True)
#        self.bias = self.add_weight(name='bias', 
#                                      shape=(self.output_dim,),
#                                      initializer='zeros',
#                                      trainable=True)
#        self.kernel = self.add_weight(name='kernel', 
#                                      shape=(input_shape[1], self.output_dim),
#                                      initializer='glorot_uniform',
#                                      trainable=True)
#        super(FM, self).build(input_shape)
#
#    def call(self, x):
#        feature =  K.dot(x,self.wight) + self.bias
#        a = K.pow(K.dot(x,self.kernel), 2)
#        b = K.dot(x, K.pow(self.kernel, 2))
#        cross = K.mean(a-b, 1, keepdims=True)*0.5
#        cross = K.repeat_elements(K.reshape(cross, (-1, 1)), self.output_dim, axis=-1)
#        return self.activate(feature + cross)
#
#    def compute_output_shape(self, input_shape):
#        return (input_shape[0], self.output_dim)
#
#
#
#def fm(x_train, x_test, y_train, y_test):
#    import keras
#    from keras.layers import Layer, Dense, Dropout,Input
#    from keras import Model,activations
#    from keras.optimizers import adam
#    import keras.backend as K
#    from sklearn.datasets import load_breast_cancer
#    K.clear_session()
#    inputs = Input(shape=(220,))
#    out = FM(3)(inputs)
#    out = Dense(50,activation="sigmoid")(out)
#    out = Dense(1,activation="linear")(out)
#    
#    model = Model(inputs=inputs, outputs=out )
#    model.compile(loss='mse',
#                          optimizer=adam(0.0001),
#                          metrics=['accuracy'])
#    model.summary()
#
#    model.fit(x_train, y_train, 
#            batch_size=1,
#            epochs=1,
#            validation_split=0.1)
#
#    model.fit(x_train, y_train)
#    
#    py = model.predict(x_test)
#    py = py.flatten()
#    #input()
#    #py = model.predict(x_test)
#    print('corr =' + str(np.corrcoef(y_test, py)[0][1]))
#    print('r2 = ' + str(r2_score(y_test, py)))


#import sys
#import cvxopt
#import cvxpy as cvx
#import numpy as np
#from pylab import *
#import math
#from cvxpy import *
#
#def opt(x_train, x_test, y_train, y_test, k):
#    '''
#
#    1. org problem
#    split dataset in to (Ai, yi) i = 1..N
#    
#    try to min (||Ai * x - yi||^2) for i = 1..N
#    
#    2. reformed problem
#    reform problem to 
#    min R0
#    where ||Ai * x - yi||^2 <= R0
#    
#    min R0
#    where x^T * Ai^T * Ai * x - 2yi^T * Ai * x + yi^T * yi <= R0
#    
#    set x_new = (x, R0) append new column
#    append Ai_new = (Ai, 1) append new column with all ones
#    
#    =>
#    min R0
#    where x_new^T * Ai_new^T * Ai_new * x_new - 2yi^T * Ai * x - R0 + yi^T * yi
#    
#    3.how to split dataset
#    
#    split dataset to k parts
#    A0:   [0, k - z]
#    A1:   [1, k - z+1]
#    A2:   [2, k - z+2]
#      :   ...
#    Az-1: [z-1, k-1]
#      
#    '''
#    
#    #k = 200
#    n = x_train.shape[1]
#    sz = x_train.shape[0] // k
#
#    #1.x = (c0, c1,...,c[n-1], bias, R0)
#    x = Variable(n + 2)
#    q0 = np.zeros((n + 2, 1))
#
#    #2. x[n+1] = R0, we need to minimize it
#    q0[n+1] = 1
#
#    objective = Minimize(q0.T * x)
#    constraints = []
#    
#    
#    
#    
#    z = 20#k - 2
#
#    
#    p1 = None
#    p2 = None
#    q1 = None
#    q2 = None
#    t1 = 0
#    t2 = 0
#
#    for j in range(k - 2):
#      #3.only train data from [s, e)
#      s = j * sz
#      #e = (j + k - z + 1) * sz
#      e = (j + 2) * sz
#      print(str(s) + ' ' + str(e))
#      
#      #4. append bias turn with all ones to b
#      b = x_train[s:e, :]
#      o = np.ones(b.shape[0])
#      b = np.column_stack((b, o))
#      
#      #5. divide by sz
#      b = b / sz * 1000
#      y = y_train[s:e] / sz * 1000
#
#      #6. by = Ai^T * yi
#      by = np.dot(b.T, y)
#      Pi_ = np.dot(b.T, b)
#
#      #7. yty = yi^T * yi
#      yty = np.dot(y.T, y)
#      c = np.zeros(b.shape[0])
#
#      #8. append one zeros columns, (for R0)
#      b = np.column_stack((b,c))
#
#
#      invpi = np.linalg.inv(Pi_)
#      optx = np.dot(invpi, by)
#      optv = np.dot(optx.T, np.dot(Pi_, optx)) - 2 * np.dot(optx.T, by)
#      yty = -optv# / 2
#
#      #9. Ai^T * Ai
#      Pi = np.dot(b.T, b)
#      qi = np.zeros((n + 2, 1))
#      qi[:(n+1), 0] = -2 * by
#      qi[n+1] = -1
#
#      #10. append contrains
#      #if (j == 1):constraints.append(quad_form(x, Pi.copy()) + qi.copy().T * x + yty.copy() <= 0)
#      constraints += [quad_form(x, Pi.copy()) + qi.copy().T * x + yty.copy() <= 0]
#      if (j == 0):
#        p1 = Pi
#        q1 = qi
#        t1 = yty
#      if (j == 1):
#        p2 = Pi
#        q2 = qi
#        t2 = yty
#      if (j == 2):
#        p3 = Pi
#        q3 = qi
#        t3 = yty
#      #break
#      
#    #constraints = [quad_form(x, p1) + q1.copy().T * x + t1 <= 0, quad_form(x, p2) + q2.T * x + t2 <= 0]
#    #constraints = [quad_form(x, p1) + q1.copy().T * x + t1 <= 0, quad_form(x, p1) + q1.T * x + t1 <= 0]
#    #constraints = [quad_form(x, p2) + q2.copy().T * x + t2 <= 0, quad_form(x, p1) + q1.T * x + t1 <= 0]
#    #constraints = [quad_form(x, p1) + q1.copy().T * x + t1 <= 0, quad_form(x, p2) + q2.T * x + t2 <= 0, quad_form(x, p1) + q1.copy().T * x + t1 <= 0]
#
#
#
#
#    #constraints = [quad_form(x, p1) + q1.copy().T * x + t1 <= 0, quad_form(x, p1) + q1.T * x + t1 <= 0]
#    #constraints = [[quad_form(x, p2) + q2.copy().T * x + t2 <= 0],[quad_form(x, p1) + q1.T * x + t1 <= 0]]
#    #print(q1)
#    #print(q2)
#    #constraints += [quad_form(x, Pi.copy()) + qi.copy().T * x + yty.copy() <= 0]
#      
#    #solve the problem
#    p = cvx.Problem(objective, constraints)
#    primal_result = p.solve(verbose=False, solver=(cvx.ECOS), reltol=0.0000001)
#    print(p.status)
#
#    #11. test set score
#    o = np.ones(x_test.shape[0])
#    localtest = np.column_stack((x_test,o))
#    py = np.dot(localtest, x.value[0:(n+1)])
#
#
#    res = np.zeros((n + 2, 1))
#    res[0:n+1, 0] = x.value[0:(n+1)]
#    X = (np.dot(res.T, np.dot(p1, res)))[0][0]
#    Y = (np.dot(q1.T, res))[0][0]
#
#    X2 = (np.dot(res.T, np.dot(p2, res)))[0][0]
#    Y2 = (np.dot(q2.T, res))[0][0]
#    
#    X3 = (np.dot(res.T, np.dot(p3, res)))[0][0]
#    Y3 = (np.dot(q3.T, res))[0][0]
#
#    #c1 = np.dot(res.T, np.dot(p1, res)) + np.dot(q1.T, x) + t1
#    #c2 = np.dot(res.T, np.dot(p2, res)) + np.dot(q2.T, x) + t2
#    print("check1=" + str(X + Y + t1))
#    print("check2=" + str(X2 + Y2 + t2))
#    print("check3=" + str(X3 + Y3 + t3))
#
#
#
#
#    testpy = list(py)
#    print('k=' + str(k) + ' corr =' + str(np.corrcoef(y_test, py)[0][1]), flush=True)
#    print('k=' + str(k) + ' r2 = ' + str(r2_score(y_test, py)), flush=True)
#    
#
#    #12. training set score
#    o = np.ones(x_train.shape[0])
#    localtrain = np.column_stack((x_train,o))
#    py = np.dot(localtrain, x.value[0:(n+1)])
#    print('k=' + str(k) + 'train corr =' + str(np.corrcoef(y_train, py)[0][1]), flush=True)
#    print('k=' + str(k) + 'train r2 = ' + str(r2_score(y_train, py)), flush=True)
#    trainpy = list(py)
#    
#    
#    #13. get regression
#
#    from sklearn.linear_model import LinearRegression
#    model = LinearRegression()
#    model = model.fit(x_train, y_train)
#    py1 = model.predict(x_train)
#    
#    for j in range(k - 1):
#      s = j * sz
#      e = (j + 1) * sz
#      #print(str(s) + ' ' + str(e))
#      lpy = py[s:e]
#      lpy1 = py1[s:e]
#      ly_train = y_train[s:e]
#      
#      print('k=' + str(k) + 'train r2 opt = ' + str(r2_score(ly_train, lpy))+ 'train r2 reg = ' + str(r2_score(ly_train, lpy1)), flush=True)
#      
#
#
#
#
#
#
#
#    allp = trainpy + testpy
#    return allp





    
    








def score(X, Ps, Qs, ts, t, n):
  downs = []
  for i in range(len(Ps)):
    lp = Ps[i]
    lq = Qs[i]
    lt = ts[i]
    a = (np.dot(X.T, np.dot(lp, X)))
    b = (np.dot(lq.T, X))
    downs.append(a + b + lt)
    if (a + b + lt > 0): return 1e12
  res = X[n + 1]
  for i in range(len(Ps)):
    res = res + (-1/t) * np.log(-downs[i])
  return res

def derivative(X, Ps, Qs, ts, t, n):
  downs = []
  for i in range(len(Ps)):
    lp = Ps[i]
    lq = Qs[i]
    lt = ts[i]
    a = (np.dot(X.T, np.dot(lp, X)))
    b = (np.dot(lq.T, X))
    downs.append(a + b + lt)

  #print(downs)
  res = np.zeros(n + 2)

  for i in range(len(Ps)):
    mul = 1 / downs[i] / t
    lp = Ps[i]
    lq = Qs[i]
    lt = ts[i]
    #lderivative = np.dot(lp, X)
    res = res + (-mul) * (2 * np.dot(lp, X) + lq.T)[0]
    #print(np.dot(lp, X) + lq.T)
    #input()
    #print('res=')
    #print(res)
    #input()
  res[n + 1] += 1
  return res

def opt1(x_train, x_test, y_train, y_test, k):
    '''

    1. org problem
    split dataset in to (Ai, yi) i = 1..N
    
    try to min (||Ai * x - yi||^2) for i = 1..N
    
    2. reformed problem
    reform problem to 
    min R0
    where ||Ai * x - yi||^2 <= R0
    
    min R0
    where x^T * Ai^T * Ai * x - 2yi^T * Ai * x + yi^T * yi <= R0
    
    set x_new = (x, R0) append new column
    append Ai_new = (Ai, 1) append new column with all ones
    
    =>
    min R0
    where x_new^T * Ai_new^T * Ai_new * x_new - 2yi^T * Ai * x - R0 + yi^T * yi
    
    3.how to split dataset
    
    split dataset to k parts
    A0:   [0, k - z]
    A1:   [1, k - z+1]
    A2:   [2, k - z+2]
      :   ...
    Az-1: [z-1, k-1]
      
    '''
    
    #k = 200
    n = x_train.shape[1]
    sz = x_train.shape[0] // k

    #1.x = (c0, c1,...,c[n-1], bias, R0)
    x = Variable(n + 2)
    q0 = np.zeros((n + 2, 1))

    #2. x[n+1] = R0, we need to minimize it
    q0[n+1] = 1

    objective = Minimize(q0.T * x)
    constraints = []
    
    
    
    
    z = 20#k - 2

    
    Ps = []
    Qs = []
    Ts = []

    for j in range(k - 1):
      #3.only train data from [s, e)
      s = j * sz
      #e = (j + k - z + 1) * sz
      e = (j + 1) * sz
      print(str(s) + ' ' + str(e))
      
      #4. append bias turn with all ones to b
      b = x_train[s:e, :]
      o = np.ones(b.shape[0])
      b = np.column_stack((b, o))
      
      #5. divide by sz
      b = b# / 10# / sz * 500
      y = y_train[s:e]# / 10# / sz * 500

      #6. by = Ai^T * yi
      by = np.dot(b.T, y)
      Pi_ = np.dot(b.T, b)

      #7. yty = yi^T * yi
      yty = np.dot(y.T, y)
      c = np.zeros(b.shape[0])

      #8. append one zeros columns, (for R0)
      b = np.column_stack((b,c))

      #9. Ai^T * Ai
      Pi = np.dot(b.T, b)
      qi = np.zeros((n + 2, 1))
      qi[:(n+1), 0] = -2 * by


      invpi = np.linalg.inv(Pi_)
      optx = np.dot(invpi, by)
      optv = np.dot(optx.T, np.dot(Pi_, optx)) - 2 * np.dot(optx.T, by)
      #print(optx)
      #print('optv=' + str(optv))
      #input()
      yty = -optv

      qi[n+1] = -1

      Ps.append(Pi) 
      Qs.append(qi) 
      Ts.append(yty)
    #print(Ps)
    #print(Qs)
    #print(Ts)
    #input()
    t = 1e4
    X = np.zeros(n + 2)
    X[n + 1] = np.max(Ts) + 0.001


    muls = [1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1]
    #minres = 1e12
    #for it in range(1000):
    #  tmp = np.random.rand(n + 2) - 0.5
    #  #print(tmp)
    #  for m in muls:
    #    try:
    #      lls = score(X + m * tmp, Ps, Qs, Ts, t, n)
    #      if (lls < minres): minres = lls
    #    except:
    #      pass
    #    try:
    #      lls = score(X -m * tmp, Ps, Qs, Ts, t, n)
    #      if (lls < minres): minres = lls
    #    except:
    #      pass
    #    try:
    #      lls = score(X -1/m * tmp, Ps, Qs, Ts, t, n)
    #      if (lls < minres): minres = lls
    #    except:
    #      pass
    #    try:
    #      lls = score(X + 1/m * tmp, Ps, Qs, Ts, t, n)
    #      if (lls < minres): minres = lls
    #    except:
    #      pass
    #print(minres)
    #exit(0)



    for it in range(10000):
      ls = score(X, Ps, Qs, Ts, t, n)
      #if (it % 100 == 0):print('local score = ' + str(ls))
      #input()
      dx = derivative(X, Ps, Qs, Ts, t, n)
      dx = dx / ((np.max(np.abs(dx))))
      #print('dx = ')
      #print(dx)
      #input()
      minv = ls
      BX = X
      for m in muls:
        try:
          #print(X)
          #print(X + m * dx)
          #input()
          lls = score(X - m * dx, Ps, Qs, Ts, t, n)
          if (lls < minv):
            minv = lls
            BX = X - m * dx
          #print('lls = ' + str(lls))
        except:
          pass
      X = BX
      if (minv == ls):break

      
      
    p1 = Ps[0]
    p2 = Ps[1]
    p3 = Ps[2]
    q1 = Qs[0]
    q2 = Qs[1]
    q3 = Qs[2]
    t1 = Ts[0]
    t2 = Ts[1]
    t3 = Ts[2]

    #11. test set score
    o = np.ones(x_test.shape[0])
    localtest = np.column_stack((x_test,o))
    py = np.dot(localtest, X[0:(n+1)])

    res = np.zeros((n + 2, 1))
    res[0:n+1, 0] = X[0:(n+1)]
    X1 = (np.dot(res.T, np.dot(p1, res)))[0][0]
    Y1 = (np.dot(q1.T, res))[0][0]

    X2 = (np.dot(res.T, np.dot(p2, res)))[0][0]
    Y2 = (np.dot(q2.T, res))[0][0]
    
    X3 = (np.dot(res.T, np.dot(p3, res)))[0][0]
    Y3 = (np.dot(q3.T, res))[0][0]

    #c1 = np.dot(res.T, np.dot(p1, res)) + np.dot(q1.T, x) + t1
    #c2 = np.dot(res.T, np.dot(p2, res)) + np.dot(q2.T, x) + t2
    print("check1=" + str(X1 + Y1 + t1))
    print("check2=" + str(X2 + Y2 + t2))
    print("check3=" + str(X3 + Y3 + t3))




    testpy = list(py)
    print('k=' + str(k) + ' corr =' + str(np.corrcoef(y_test, py)[0][1]), flush=True)
    print('k=' + str(k) + ' r2 = ' + str(r2_score(y_test, py)), flush=True)
    

    #12. training set score
    o = np.ones(x_train.shape[0])
    localtrain = np.column_stack((x_train,o))
    py = np.dot(localtrain, X[0:(n+1)])
    print('k=' + str(k) + 'train corr =' + str(np.corrcoef(y_train, py)[0][1]), flush=True)
    print('k=' + str(k) + 'train r2 = ' + str(r2_score(y_train, py)), flush=True)
    trainpy = list(py)
    
    
    #13. get regression

    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model = model.fit(x_train, y_train)
    py1 = model.predict(x_train)
    
    for j in range(k - 1):
      s = j * sz
      e = (j + 1) * sz
      #print(str(s) + ' ' + str(e))
      lpy = py[s:e]
      lpy1 = py1[s:e]
      ly_train = y_train[s:e]
      
      print('k=' + str(k) + 'train r2 opt = ' + str(r2_score(ly_train, lpy))+ 'train r2 reg = ' + str(r2_score(ly_train, lpy1)), flush=True)
      







    allp = trainpy + testpy
    return allp

      
      


#np.random.seed(1)
#
#a = np.random.rand(1000, 20)
#b = np.random.rand(1000)
#
#opt(a, a, b, b, 4)




#svm_c_one(train_X,test_X,train_y,test_y)
#RF(train_X,test_X,train_y,test_y)
#lasso(train_X,test_X,train_y,test_y, all_X, all_y, a.index)

#ridge(train_X,test_X,train_y,test_y)
reg(train_X,test_X,train_y,test_y)
#reg(train_X,all_X,train_y,all_y)



#RF(train_X,test_X,train_y,test_y)
#svr(train_X,test_X,train_y,test_y)
#enet(train_X,test_X,train_y,test_y)

#opt(train_X,test_X,train_y,test_y, 2)

#for k in range(6,20):
#  py = opt(train_X,test_X,train_y,test_y, k)
#  #break
#res = pd.DataFrame({'dt':raw['dt'],'Ticker':raw['Ticker'],'sig':py, }, index=a.index)
#res.to_csv('yzhan.csv')

