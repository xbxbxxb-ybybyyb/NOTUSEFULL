import numpy as np
import pandas as pd
from scipy.stats import skew,kurtosis


def drop_duplicate_col_with_diff_name(df):
    tmp = pd.DataFrame()
    tmp['sum'] = df.sum()
    tmp['mean'] = df.mean()
    tmp['var'] = df.var()
    tmp1 = tmp.drop_duplicates()
    col = tmp1.index.tolist()
    df1 = df.iloc[:,col]
    return df1

# combine features in a category with different windows
def get_features_with_windows(df,function,n_list):
    feats = pd.DataFrame()
    # features with 1 window
    try: 
        for i in range(len(n_list)):
            df1 = function(df,n_list[i])
            feats = pd.concat([feats,df1], axis=1)
    # features with 2 windows
    except: 
        try:
            for i in range(len(n_list)):
                for j in range(len(n_list)):
                    df1 = function(df,n_list[i],n_list[j])
                    feats = pd.concat([feats,df1], axis=1)
        except:
            feats = function(df)
    # drop duplicate column with same column names
    feats = feats.loc[:,~feats.columns.duplicated()]
    # drop duplicate column with different column names
    # com_feat = drop_duplicate_col_with_diff_name(feats)
    return feats


# 净委买增额
def get_cat1(df,n1,n2):  # n1-diff window, n2-rolling window
    new = np.zeros([df.shape[0],5])
    raw = np.array(df[['totalbidqty','totalofferqty','totalvolumetrade']])
    new[n1:,0] = (raw[n1:,0]-raw[:-n1,0])-(raw[n1:,1]-raw[:-n1,1])  #c1 absqty_mov 
    new[n1:,1] = raw[n1:,2]-raw[:-n1,2]  #c2 volume
    new[n1:,2] = new[n1:,0]/new[n1:,1]  #c3 absqty_mov_ratio
    new[(new[:,1]==0),2] = new[(new[:,1]==0),0]/0.1
    
    absqty_mov_roll = np.concatenate([np.full([n1+n2-1,], np.nan), np.convolve(new[n1:,0],np.ones(n2),'valid')/n2], axis=0) 
    absqty_mov_ratio_roll = np.concatenate([np.full([n1+n2-1,], np.nan), np.convolve(new[n1:,2],np.ones(n2),'valid')/n2], axis=0) 
    
    new[:,3] = absqty_mov_roll  #c4 absqty_mov_roll
    new[:,4] = absqty_mov_ratio_roll  #c5 absqty_mov_ratio_roll
    new = np.delete(new,1,1) # delete c2 volumn
    df1 = pd.DataFrame(new,columns=(
        f'absqty_mov_{n1}',f'absqty_mov_r_{n1}',f'absqty_mov_{n1}_{n2}',f'absqty_mov_r_{n1}_{n2}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n1).index,df1.columns[0:2]]=np.nan
    df1.loc[df1.groupby('mddate').head(n1+n2).index,df1.columns[2:4]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1 

# 方差/偏度/峰度
def get_cat2(df,n1,n2):    
    df1 = pd.DataFrame(columns=(f'ret_last{n1}',f'ret_mid{n1}',f'var_last{n1}_{n2}',f'var_mid{n1}_{n2}',
        f'skew_last{n1}_{n2}',f'skew_mid{n1}_{n2}',f'kurt_last{n1}_{n2}',f'kurt_mid{n1}_{n2}'))
    
    df1[f'ret_last{n1}'] = (df['lastpx'] - df['lastpx'].shift(n1)) / df['lastpx'].shift(n1)
    df1[f'ret_mid{n1}'] = (((df['sell1price'])+df['buy1price']) - (df['sell1price'].shift(n1)+df['buy1price'].shift(n1))) / (df['sell1price'].shift(n1)+df['buy1price'].shift(n1))
    df1[f'var_last{n1}_{n2}'] = (df1[f'ret_last{n1}'] ** 2).rolling(n2).sum()
    df1[f'var_mid{n1}_{n2}'] = (df1[f'ret_mid{n1}'] ** 2).rolling(n2).sum()
    df1[f'skew_last{n1}_{n2}'] = ((df1[f'ret_last{n1}'] ** 3).rolling(n2).sum()) * (n2 ** 0.5) / (df1[f'var_last{n1}_{n2}'] ** 3/2)
    df1[f'skew_mid{n1}_{n2}'] = ((df1[f'ret_mid{n1}'] ** 3).rolling(n2).sum()) * (n2 ** 0.5) / (df1[f'var_mid{n1}_{n2}'] ** 3/2)
    #写错了吧？
    '''
    df[f'kurt_last{n1}_{n2}'] = ((df1[f'ret_last{n1}'] ** 4).rolling(n2).sum()) * n2 / (df1[f'var_last{n1}_{n2}'] ** 2)
    df[f'kurt_mid{n1}_{n2}'] = ((df1[f'ret_mid{n1}'] ** 4).rolling(n2).sum()) * n2 / (df1[f'var_mid{n1}_{n2}'] ** 2)
    '''
    df1[f'kurt_last{n1}_{n2}'] = ((df1[f'ret_last{n1}'] ** 4).rolling(n2).sum()) * n2 / (df1[f'var_last{n1}_{n2}'] ** 2)
    df1[f'kurt_mid{n1}_{n2}'] = ((df1[f'ret_mid{n1}'] ** 4).rolling(n2).sum()) * n2 / (df1[f'var_mid{n1}_{n2}'] ** 2)    
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n1).index,df1.columns[0:2]]=np.nan
    df1.loc[df1.groupby('mddate').head(n1+n2).index,df1.columns[2:8]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# 买卖挂单强度
def get_cat3(df,n):
    new = np.zeros([df.shape[0],3])
    buy = 0
    sell = 0
    for i in range(1,11):
        a = 'buy' + str(i) +'price'
        b = 'buy' + str(i) +'orderqty'
        c = 'sell' + str(i) +'price'
        d = 'sell' + str(i) +'orderqty'
        buy += df[a] * df[b]
        sell += df[c] * df[d]
    new[:,0] = buy-sell 
    
    buy_roll_sum = np.concatenate([np.full([n-1,], np.nan), np.convolve(buy,np.ones(n),'valid')], axis=0) 
    buy_roll_mean = np.concatenate([np.full([n-1,], np.nan), np.convolve(buy,np.ones(n),'valid')/n], axis=0) 
    sell_roll_sum = np.concatenate([np.full([n-1,], np.nan), np.convolve(sell,np.ones(n),'valid')], axis=0) 
    sell_roll_mean = np.concatenate([np.full([n-1,], np.nan), np.convolve(sell,np.ones(n),'valid')/n], axis=0) 
    
    new[:,1] = buy_roll_sum - sell_roll_sum
    new[:,2] = buy_roll_mean / sell_roll_mean
    df1 = pd.DataFrame(new,columns=(
        f'vol_diff{n}',f'vol_diff_roll{n}',f'vol_diff_roll_mean{n}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n).index,df1.columns[0:3]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1
  
# MACD
def get_cat4(df,n=9): # n1<n2
    n1=12
    n2=26
    new = np.zeros([df.shape[0],3])
    k = df['lastpx'].ewm(span=n1, adjust=False).mean()
    d = df['lastpx'].ewm(span=n2, adjust=False).mean()
    macd = k - d
    macd_s = macd.ewm(span=n, adjust=False).mean()
    new[:,0] = macd
    new[:,1] = macd_s
    new[:,2] = new[:,0]-new[:,1]
    df1 = pd.DataFrame(new,columns=(
        f'macd',f'macd_s{n}',f'macd_h{n}'))
    return df1

# 情绪因子
def get_cat5(df,n1,n2):
    new = np.zeros([df.shape[0],9])
    raw = np.array(df[['lastpx','sell1price','buy1price','totalbidqty','totalofferqty']])
    df['sellpx_shift'] = df['sell1price'].shift(n1)
    df['buypx_shift'] = df['buy1price'].shift(n1)
    new[:,0] = df.apply(lambda x: 1 if x['lastpx']>=x['sellpx_shift'] else 0, axis=1)
    new[:,1] = df.apply(lambda x: 1 if x['lastpx']>=x['buypx_shift'] else 0, axis=1)
    new[n1:,1] = new[n1:,0] * (raw[n1:,3]-raw[:-n1,3])
    new[n1:,2] = new[n1:,0] * ((raw[n1:,3]-raw[:-n1,3]) -(raw[n1:,4]-raw[:-n1,4]))
    new[np.where(new[:,1]>0),3] = new[np.where(new[:,1]>0),1]
    new[np.where(new[:,1]<0),4] = -new[np.where(new[:,1]<0),1]
    new[np.where(new[:,2]>0),5] = new[np.where(new[:,2]>0),2]
    new[np.where(new[:,2]<0),6] = -new[np.where(new[:,2]<0),2]
    
    mean1 = np.concatenate([np.full([n2-1,], np.nan), np.convolve(new[:,3],np.ones(n2),'valid')], axis=0)
    mean2 = np.concatenate([np.full([n2-1,], np.nan), np.convolve(new[:,4],np.ones(n2),'valid')], axis=0)
    mean3 = np.concatenate([np.full([n2-1,], np.nan), np.convolve(new[:,5],np.ones(n2),'valid')], axis=0)
    mean4 = np.concatenate([np.full([n2-1,], np.nan), np.convolve(new[:,6],np.ones(n2),'valid')], axis=0)
    
    new[:,7] = mean1/mean2
    new[:,8] = mean3/mean4
    
    df1 = pd.DataFrame(new,columns=(
        f'sentiment_flag{n1}',f'sentiment_vol{n1}',f'sentiment_vols{n1}',f'pos1{n1}',f'cau1{n1}',
        f'pos2{n1}',f'cau2{n1}',f'pbcb{n1}_{n2}',f'pbcbs{n1}_{n2}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n1).index,df1.columns[0:7]]=np.nan
    df1.loc[df1.groupby('mddate').head(n1+n2).index,df1.columns[7:9]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# 最高价最低价
def get_cat6(df,n):
    new = np.zeros([df.shape[0],4])
    new[:,0] = df['highpx']-df['lastpx']
    new[:,1] = df['lowpx']-df['lastpx']
    new[np.where(new[:,1]!=0),2] = new[np.where(new[:,1]!=0),0]/new[np.where(new[:,1]!=0),1]
    
    mean1 = np.concatenate([np.full([n-1,], np.nan), np.convolve(new[:,0],np.ones(n),'valid')], axis=0)
    mean2 = np.concatenate([np.full([n-1,], np.nan), np.convolve(new[:,1],np.ones(n),'valid')], axis=0)
    
    new[:,3] = mean1/mean2
    df1 = pd.DataFrame(new,columns=(
        'high_diff','low_diff','highlow',f'highlow_roll{n}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n).index, df1.columns[3]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# K值
def get_cat7(df,n1,n2):
    new = np.zeros([df.shape[0],4])
    new[:,0] = df['lastpx'].rolling(n1).max()
    new[:,1] = df['lastpx'].rolling(n1).min()
    new[:,2] = (df['lastpx']-new[:,0])/(new[:,0]-new[:,1])
    tmp = pd.DataFrame(new[:,2])
    new[:,3] = tmp.iloc[:,0].ewm(span=n2, adjust=False, min_periods=n2).mean() 
    df1 = pd.DataFrame(new,columns=(
        f'px_high_roll{n1}',f'px_low_roll{n1}',f'rsv{n1}_{n2}',f'k{n1}_{n2}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n1).index,df1.columns[0:2]]=np.nan
    df1.loc[df1.groupby('mddate').head(n1+n2).index,df1.columns[2:4]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# OBV 
def get_cat8(df,n):
    new = np.zeros([df.shape[0],2])
    tmp = np.array(df[['lastpx','totalvolumetrade']])
    df['lastpx_shift'] = df['lastpx'].shift(n)
    new[:,0] = df.apply(lambda x: 1 if x['lastpx']>x['lastpx_shift'] else (-1 if x['lastpx']<x['lastpx_shift'] else 0),axis=1)
    new[n:,1] = new[n:,0]*(tmp[n:,1]-tmp[:-n,1])

    df1 = pd.DataFrame(new,columns=(
        f'obv_flag{n}',f'voltrade{n}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n).index,df1.columns]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# AD
def get_cat9(df,n1,n2):
    new = np.zeros([df.shape[0],4])
    df['flag'] = (df['lastpx']*2-df['highpx']-df['lowpx']) * (df['highpx']-df['lowpx'])
    new[:,0] = df['flag']
    df['flag2'] =  (df['lastpx']*2-df['lastpx'].rolling(n1).max()-df['lastpx'].rolling(n1).min()) * (df['lastpx'].rolling(n1).max()-df['lastpx'].rolling(n1).min())
    new[:,1] = df['flag2']
    df['volume'] = df['totalvolumetrade'].diff()
    
    df['ad1'] = 0
    df['ad2'] = 0
    '''
    for i in range(n2, df.shape[0]):
        df['ad1'][i] = df['ad1'][i-1] + df['flag'][i]*df['volume'][i]
        df['ad2'][i] = df['ad2'][i-1] + df['flag2'][i]*df['volume'][i]
    '''
    '''
    #有些index不连续 上面的写法会卡住
    for i in range(n2, df.shape[0]):
        df['ad1'].iloc[i] = df['ad1'].iloc[i-1] + df['flag'].iloc[i]*df['volume'].iloc[i]
        df['ad2'].iloc[i] = df['ad2'].iloc[i-1] + df['flag2'].iloc[i]*df['volume'].iloc[i]
   '''
    
    #原来的for 循环太慢 改用cumsum
    df['ad1'].iloc[n2:]=(df['flag'].iloc[n2:]*df['volume'].iloc[n2:]).cumsum()
    df['ad2'].iloc[n2:]=(df['flag2'].iloc[n2:]*df['volume'].iloc[n2:]).cumsum()
    
    new[:,2] = df['ad1']
    new[:,3] = df['ad2']
       
    df1 = pd.DataFrame(new,columns=(
        f'clv',f'clv_s{n1}',f'ad{n1}_{n2}',f'ad_s{n1}_{n2}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n1).index,df1.columns[1]]=np.nan
    df1.loc[df1.groupby('mddate').head(n1+n2).index,df1.columns[2:4]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# 聪明钱
def get_cat10(df,n1,n2):
    new = np.zeros([df.shape[0],3])
    raw = np.array(df[['lastpx','totalvolumetrade']])
    new[n1:,0] = (raw[n1:,0]-raw[:-n1,0])/raw[:-n1,0]  # lastpx_mov
    new[n2:,1] = raw[n2:,1]-raw[:-n2,1]   # volume
    new[:,2] = new[:,0] / (new[:,1] ** (0.5))
    new[(new[:,1]==0),2] = new[(new[:,1]==0),0]/(0.1** (0.5))
    df1 = pd.DataFrame(new,columns=(
        f'ret_last{n1}',f'volumn{n2}',f'st{n1}_{n2}'))
    df1['mddate'] = df['mddate']
    df1.loc[df1.groupby('mddate').head(n1).index,df1.columns[0:2]]=np.nan
    df1.loc[df1.groupby('mddate').head(n1+n2).index,df1.columns[2]]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# Values
def get_cat11(df): 
    # 1-10: ask_i_value ~~ sellqty/(buyqty+sellqty)
    # 11-20: bid_i_value ~~ buyqty/(buyqty+sellqty)
    # 21-30: spread ~~ ask_i_value - bid_i_value
    # 31-39: ask_diff ~~ ask_i+1_value - ask_i_value
    # 40-48: bid_diff ~~ bid_i+1_value - bid_i+1_value
    # 49: acc_diff ~~  sum(ask_i_value - bid_i_value)
    # 50: ask_mean ~~ mean(ask_i_value)
    # 51: bid_mean ~~ mean(bid_i_value)
    values = np.full([df.shape[0],51], np.nan)
    for i in range(1,11):
        ask_value = df[f'sell{i}orderqty']/(df[f'buy{i}orderqty']+df[f'sell{i}orderqty'])
        bid_value = df[f'buy{i}orderqty']/(df[f'buy{i}orderqty']+df[f'sell{i}orderqty'])
        spread = ask_value - bid_value
        values[:,i-1] = ask_value
        values[:,i+9] = bid_value
        values[:,i+19] = spread
    for i in range(9):
        ask_diff = values[:,i+1]-values[:,i]
        bid_diff = values[:,i+10+1]-values[:,i+10]
    acc_diff = 0
    sum_ask = 0
    sum_bid = 0
    for i in range(10):    
        values[:,i+29] = ask_diff
        values[:,i+39] = bid_diff 
        acc_diff += values[:,i] - values[:,i+10]
        sum_ask += values[:,i]
        sum_bid += values[:,i+10]
    values[:,48] = acc_diff
    values[:,49] = sum_ask/10
    values[:,50] = sum_bid/10
    
    columns = []
    for i in range(1,11):
        columns.append(f'ask_{i}_value')
    for i in range(1,11):
        columns.append(f'bid_{i}_value')
    for i in range(1,11):
        columns.append(f'ask_bid_{i}_value_spread')
    for i in range(1,10):
        columns.append(f'ask_{i+1}&{i}_value_diff')
    for i in range(1,10):
        columns.append(f'bid_{i+1}&{i}_value_diff') 
    columns.append(f'accumulate_value_diff')
    columns.append('ask_value_mean')
    columns.append('bid_value_mean')       
    df1 = pd.DataFrame(values,columns=columns)
    return df1

# Values_MA 
def get_cat12(df, N):
    # N: rolling window of value
    # 1-10: ask_i_value's mean at [t-N,t] - ask_i_value
    # 11-20: bid_i_value's mean at [t-N,t] - bid_i_value
    # 21-30: ask_i_value's mean at [t-N,t] - bid_i_value's mean at [t-N,t]
    ma = np.full([df.shape[0],30], np.nan)
    values = np.array(get_cat11(df))[:,:20]
    for i in range(10):
        ask_rolling_mean = np.concatenate([np.full([N-1,], np.nan), np.convolve(values[:,i],np.ones(N),'valid')/N], axis=0) 
        bid_rolling_mean = np.concatenate([np.full([N-1,], np.nan), np.convolve(values[:,i+10],np.ones(N),'valid')/N], axis=0) 
        ma[:,i] = ask_rolling_mean - values[:,i]
        ma[:,i+10] = bid_rolling_mean - values[:,i+10]
        ma[:,i+20] = ask_rolling_mean - bid_rolling_mean
    
    columns = []
    for i in range(1,11):
        columns.append(f'ask_{i}_value_ma_{N}')
    for i in range(1,11):
        columns.append(f'bid_{i}_value_ma_{N}')
    for i in range(1,11):
        columns.append(f'ask_bid_{i}_value_ma_diff_{N}')
    df1 = pd.DataFrame(ma,columns=columns)
    df1['mddate'] = df['mddate']
    df1[columns].loc[df1.groupby('mddate').head(N).index]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# Basics
def get_cat13(df):
    # 1-10: midprice_i 
    # 11: ask price mean
    # 12: bid price mean
    # 13: ask quantity mean
    # 14: bid quantity mean
    # 15: accumulate difference of price
    # 16: accumulate difference of quantity
    # 17: last price
    basics = np.full([df.shape[0],17], np.nan)
    ask_px_sum = 0
    bid_px_sum = 0
    ask_qty_sum = 0
    bid_qty_sum = 0
    acc_diff_px = 0
    acc_diff_qty = 0
    for i in range(1,11):
        midprice = (df[f'sell{i}price']+df[f'buy{i}price'])/2
        basics[:,i-1] = midprice
        ask_px_sum += df[f'sell{i}price']
        bid_px_sum += df[f'buy{i}price']
        ask_qty_sum += df[f'sell{i}orderqty']
        bid_qty_sum += df[f'buy{i}orderqty']
        acc_diff_px += df[f'sell{i}price'] - df[f'buy{i}price']
        acc_diff_qty += df[f'sell{i}orderqty'] - df[f'buy{i}orderqty']
    basics[:,10] = ask_px_sum/10
    basics[:,11] = bid_px_sum/10
    basics[:,12] = ask_qty_sum/10
    basics[:,13] = bid_qty_sum/10
    basics[:,14] = acc_diff_px
    basics[:,15] = acc_diff_qty  
    basics[:,16] = df['lastpx']
    columns = []
    for i in range(1,11):
        columns.append(f'midprice_{i}')
    columns.append('ask_price_mean')
    columns.append('bid_price_mean')
    columns.append('ask_qty_mean')
    columns.append('bid_qty_mean')
    columns.append('acc_price_diff')
    columns.append('acc_qty_diff')
    columns.append('last_px')
    df1 = pd.DataFrame(basics,columns=columns)
    return df1
    
# Differences
def get_cat14(df, N):
    # N: window
    # 1-10: ask i price difference 
    # 11-20: bid i price difference
    # 21-30: ask i qty difference
    # 31-40: bid i qty difference
    # 41-50: ask i value difference
    # 51-60: bid i value difference
    # 61-70: ask_i_px_diff * ask_i_qty_diff
    # 71-80: bid_i_px_diff * bid_i_qty_diff
    diffs = np.full([df.shape[0],80], np.nan)
    values = np.array(get_cat11(df))[:,:20]
    nans = np.full([N,], np.nan)
    for i in range(1,11):
        diffs[:,i-1] = df[f'sell{i}price'] - df[f'sell{i}price'].shift(N)
        diffs[:,i+9] = df[f'buy{i}price'] - df[f'buy{i}price'].shift(N)
        diffs[:,i+19] = df[f'sell{i}orderqty'] - df[f'sell{i}orderqty'].shift(N)
        diffs[:,i+29] = df[f'buy{i}orderqty'] - df[f'buy{i}orderqty'].shift(N)
        diffs[:,i+39] = np.concatenate([nans, (values[N:,i-1] - values[:-N,i-1])])
        diffs[:,i+49] = np.concatenate([nans, (values[N:,i+9] - values[:-N,i+9])])
        diffs[:,i+59] = diffs[:,i-1]*diffs[:,i+19]
        diffs[:,i+69] = diffs[:,i+9]*diffs[:,i+29]
    
    columns = []
    for i in range(1,11):
        columns.append(f'ask_{i}_price_diff_{N}')
    for i in range(1,11):
        columns.append(f'bid_{i}_price_diff_{N}')
    for i in range(1,11):
        columns.append(f'ask_{i}_qty_diff_{N}')
    for i in range(1,11):
        columns.append(f'bid_{i}_qty_diff_{N}')
    for i in range(1,11):
        columns.append(f'ask_{i}_value_diff_{N}')
    for i in range(1,11):
        columns.append(f'bid_{i}_value_diff_{N}')    
    for i in range(1,11):
        columns.append(f'ask_{i}_pxqty_diff_{N}')
    for i in range(1,11):
        columns.append(f'bid_{i}_pxqty_diff_{N}')        
        
    df1 = pd.DataFrame(diffs,columns=columns)
    df1['mddate'] = df['mddate']
    df1[columns].loc[df1.groupby('mddate').head(N).index]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1

# Withdraws
def get_cat15(df):
    # 1-3: withdraw buy - withdraw sell: number, amount, money
    # 4-6: withdraw buy + withdraw sell: number, amount, money
    # 7-9: withdraw buy / (withdraw_buy + withdraw_sell): number, amount, money
    # 10-12: withdraw buy / (withdraw_buy - withdraw_sell): number, amount, money
    withdraws = np.full([df.shape[0],12], np.nan)
    withdraw_buy = np.array(df[['withdrawbuynumber','withdrawbuyamount','withdrawbuymoney']])
    withdraw_sell = np.array(df[['withdrawsellnumber','withdrawsellamount','withdrawsellmoney']])
    withdraws[:,:3] = withdraw_buy - withdraw_sell
    withdraws[:,3:6] = withdraw_buy + withdraw_sell
    withdraws[:,6:9] = withdraw_buy / (withdraw_buy + withdraw_sell)
    withdraws[:,9:12] =  withdraw_buy / (withdraw_buy - withdraw_sell)
    df1 = pd.DataFrame(withdraws,columns=('withdraw_number_diff','withdraw_amount_diff','withdraw_money_diff','withdraw_number_sum','withdraw_amount_sum','withdraw_money_sum','withdraw_number_ratio_sum','withdraw_amount_ratio_sum','withdraw_money_ratio_sum','withdraw_number_ratio_diff','withdraw_amount_ratio_diff','withdraw_money_ratio_diff'))
    return df1 

# MAs
def get_cat16(df, N): 
    # N: window (20,50,100,200)
    # 1: laspx MA in previous N ticks
    # 2: laspx EMA in previous N ticks
    ## An exponential moving average (EMA), also known as an exponentially weighted moving average (EWMA), is a first-order infinite impulse response filter that applies weighting factors which decrease exponentially.
    # 3: MACD: laspx EMA in previous N ticks - laspx EMA in previous 2N ticks
    ## Moving average convergence divergence (MACD) is a trend-following momentum indicator that shows the relationship between two moving averages of prices. The MACD is calculated by subtracting the 26-day exponential moving average (EMA) from the 12-day EMA
    mas = np.full([df.shape[0],3], np.nan)
    mas[:,0] = df['lastpx'].rolling(N).mean()
    ewma = pd.Series.ewm
    mas[:,1] = ewma(df["lastpx"], span=N).mean()
    mas[:,2] = ewma(df["lastpx"], span=N).mean() - ewma(df["lastpx"], span=2*N).mean()
    
    df1 = pd.DataFrame(mas,columns=(f'ma_{N}',f'ema_{N}',f'macd_{N}'))
    df1['mddate'] = df['mddate']
    cols = df1.columns
    df1[cols].loc[df1.groupby('mddate').head(N).index]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1 

# RSI
def get_cat17(df, N):
    # N: window
    # 1: RSI
    ## The Relative Strength Index (RSI), developed by J. Welles Wilder, is a momentum oscillator that measures the speed and change of price movements. The RSI oscillates between zero and 100. Traditionally the RSI is considered overbought when above 70 and oversold when below 30. Signals can be generated by looking for divergences and failure swings. RSI can also be used to identify the general trend.
    deltas = np.diff(df['lastpx'])
    seed = deltas[:N+1]
    up = seed[seed>=0].sum()/N
    down = -seed[seed<0].sum()/N
    rs = up/down
    rsi = np.zeros_like(df['lastpx'])
    rsi[:N] = 100. - 100./(1.+rs)
    for i in range(N, len(df['lastpx'])):
        delta = deltas[i-1] # cause the diff is 1 shorter
        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(N-1) + upval)/N
        down = (down*(N-1) + downval)/N
        rs = up/down
        rsi[i] = 100. - 100./(1.+rs)       
    df1 = pd.DataFrame(rsi,columns=[f'rsi_{N}'])
    df1['mddate'] = df['mddate']
    cols = df1.columns
    df1[cols].loc[df1.groupby('mddate').head(N).index]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1 

# Bollinger Bands
def get_cat18(df, N, price='lastpx', no_of_std=2):
    # Bollinger Bands are a type of statistical chart characterizing the prices and volatility over time of a financial instrument or commodity, using a formulaic method propounded by John Bollinger in the 1980s. Financial traders employ these charts as a methodical tool to inform trading decisions, control automated trading systems, or as a component of technical analysis. Bollinger Bands display a graphical band (the envelope maximum and minimum of moving averages, similar to Keltner or Donchian channels) and volatility (expressed by the width of the envelope) in one two-dimensional chart.
    # N: window of MA
    # price: last price or mid-price, default='lastpx'
    # no_of_std: default=2    
    # 1: Bollinger Bands--MA
    # 2: Bollinger Bands--lower band
    # 3: Bollinger Bands--upper band
    # 4-6: relative location of price vs. BBs-MA, lower band, higher band   --   >:1, =:0, <:-1 (相对位置)
    # 7-9: relative distance of price vs. BBs-MA, lower band, higher band  
    # 10: weighted relative location: MA+3*UP+3*LO
    # 11: weighted relative distance: MA+3*UP+3*LO 
    # 11-13: price cross BBs-MA, lower band, higher band   --  upwards cross:1, downwards cross:-1, no cross:0
    # 14: weighted price cross: MA+3*UP+3*LO
    bbs = np.full([df.shape[0], 14], np.nan)
    ma = df[price].rolling(N).mean()
    std = df[price].rolling(N).std() 
    bbs[:,0] = ma
    bbs[:,1] = ma + no_of_std * std #upper band
    bbs[:,2] = ma - no_of_std * std #lower band
    px = np.array(df[price])
    for i in range(3):
        bbs[:,i+3] = np.where(px>bbs[:,i], 1, bbs[:,i])
        bbs[:,i+3] = np.where(px==bbs[:,i], 0, bbs[:,i])
        bbs[:,i+3] = np.where(px<bbs[:,i], -1, bbs[:,i])
    bbs[:,6] = px-bbs[:,0]
    bbs[:,7] = px-bbs[:,1]
    bbs[:,8] = px-bbs[:,2]
    bbs[:,9] = bbs[:,6]+3*bbs[:,7]+3*bbs[:,8]
    bbs[:,10:13] = np.concatenate([np.full([1,3], np.nan), (bbs[1:,3:6]-bbs[:-1,3:6])])
    bbs[:,13] = bbs[:,10] + 3*bbs[:,11] +3*bbs[:,12]    
    df1 = pd.DataFrame(bbs,columns=(
        f'ma_band_{N}',f'lower_band_{N}',f'upper_band_{N}',f'price_vs_ma_{N}',f'price_vs_lo_{N}',f'price_vs_up_{N}',f'price_vs_bb_weighted_{N}',f'px_ma_distance_{N}',f'px_lo_distance_{N}',f'px_up_distance_{N}',f'price_cross_ma_{N}',f'price_cross_lo_{N}',f'price_cross_up_{N}',f'price_cross_bb_weighted_{N}'))
    df1['mddate'] = df['mddate']
    cols = df1.columns
    df1[cols].loc[df1.groupby('mddate').head(N).index]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1 

# Order Imbalance
def get_cat19(df):
    # 1: Order imblance: buy~sum(px*qty)/sum(qty) - sell~sum(px*qty)/sum(qty)
    # 2: Order imbalance ratio: (buy~sum(px*qty)/sum(qty) - sell~sum(px*qty)/sum(qty)) / (buy~sum(px*qty)/sum(qty) + sell~sum(px*qty)/sum(qty))
    # 3: Volume order imbalance ratio: (buy~sum(qty) - sell~sum(qty)) / (buy~sum(qty) + sell~sum(qty))
    # 4: Weighted volume oir imbalance ratio: (buy~weighted_sum(qty) - sell~weighted_sum(qty)) / (buy~weighted_sum(qty) + sell~weighted_sum(qty))
        ## weighted_sum: 10*{1}+9*{2}+8*{3}+7*{4}+6*{5}+5*{6}+4*{7}+3*{8}+2*{9}+1*{10}
    vois = np.full([df.shape[0], 4], np.nan)
    px_qty = np.full([df.shape[0],40], np.nan)
    for i in range(1,11):
        px_qty[:,i-1] = df[f'buy{i}price']
        px_qty[:,i+9] = df[f'buy{i}orderqty']
        px_qty[:,i+19] = df[f'sell{i}price']
        px_qty[:,i+29] = df[f'sell{i}orderqty'] 
    buy_product = np.sum(px_qty[:,:10]*px_qty[:,10:20],axis=1)
    sell_product = np.sum(px_qty[:,20:30]*px_qty[:,30:40],axis=1)
    vois[:,0] = buy_product/np.sum(px_qty[:,:10],axis=1) - sell_product/np.sum(px_qty[:,20:30],axis=1)
    vois[:,1] = vois[:,0] / (buy_product/np.sum(px_qty[:,:10],axis=1) + sell_product/np.sum(px_qty[:,20:30],axis=1))
    vois[:,2] = (np.sum(px_qty[:,10:20], axis = 1) - np.sum(px_qty[:,30:40], axis = 1)) / (np.sum(px_qty[:,10:20], axis = 1) + np.sum(px_qty[:,30:40], axis = 1))
    def get_weighted_qty(qty):
        weighted_qty = 10*qty[:,0]+9*qty[:,1]+8*qty[:,2]+7*qty[:,3]+6*qty[:,4]+5*qty[:,5]+4*qty[:,6]+3*qty[:,7]+2*qty[:,8]+1*qty[:,9]
        return weighted_qty
    vois[:,3] = (get_weighted_qty(px_qty[:,10:20]) - get_weighted_qty(px_qty[:,30:40])) / (get_weighted_qty(px_qty[:,10:20]) + get_weighted_qty(px_qty[:,30:40]))
    
    df1 = pd.DataFrame(vois,columns=('oi','oir','voir','weighted_voir'))
    return df1 

# Abnormal spreads & depths
def get_cat20(df, N1, N2, span=1000):
    # N1: 算abnormal的window
    # N2: depth&spread's window
    # span: 算abnormal的benchmark的span
    # 1: depth  ~~  mean(sell1&buy1 ~ px * qty)
    # 2: depth with window N2  ~~  mean(depth in previous N2 ticks)
    # 3: abnormal depth  ~~  depth - benchmark_depth(N1 ticks前span ticks内的mean depth)
    # 4: abnormal depth with window N2  ~~  depth with window - benchmark_depth(N1 ticks前span ticks内的mean depth)  
    # 5: effective spread  ~~  mean(buy&sell ~ 2|i_px-midpx|/midpx)
    # 6: effective spread with window N2  ~~  mean(spread in previous N2 ticks)
    # 7: anbormal effective spread  ~~  effective spread - benchmark_spread(N ticks前span ticks内的mean effective spread)
    # 8: abnormal effective spread with window N2  ~~  effective spread with window- benchmark_spread(N ticks前span ticks内的mean effective spread)
    ds = np.full([df.shape[0],8], np.nan)
    df['depth'] = (df['buy1price']*df['buy1orderqty'] + df['sell1price']*df['sell1orderqty'])/2
    df['depth_window'] = df['depth'].rolling(N2).mean()
    df['depth_benchmark'] = df['depth'].rolling(span).mean().shift(N1)
    ds[:,0] = df['depth']
    ds[:,1] = df['depth_window']
    ds[:,2] = df['depth'] - df['depth_benchmark']
    ds[:,3] = df['depth_window'] - df['depth_benchmark']
    df['spread'] = 0
    for i in range(1,11):
        df['spread'] = df['spread'] + 2*np.abs(df[f'buy{i}price']-df['midpx'])/df['midpx'] + 2*np.abs(df[f'sell{i}price']-df['midpx'])/df['midpx']
    df['spread_window'] = df['spread'].rolling(N2).mean()
    df['spread_benchmark'] = df['spread'].rolling(span).mean().shift(N1)
    ds[:,4] = df['spread']
    ds[:,5] = df['spread_window']
    ds[:,6] = df['spread'] - df['spread_benchmark']
    ds[:,7] = df['spread_window'] - df['spread_benchmark']
    
    df1 = pd.DataFrame(ds,columns=(
        f'depth',f'depth_with_win_{N2}',f'abn_{N1}_depth',f'abn_{N1}_depth_with_win_{N2}',f'espread',f'espread_with_win_{N2}',f'abn_{N1}_espread',f'abn_{N1}_espread_with_win_{N2}'))
    df1['mddate'] = df['mddate']
    cols = [f'depth_with_win_{N2}',f'abn_{N1}_depth_with_win_{N2}',f'espread_with_win_{N2}',f'abn_{N1}_espread_with_win_{N2}']
    df1[cols].loc[df1.groupby('mddate').head(N2).index]=np.nan
    df1 = df1.drop(['mddate'],axis = 1)
    return df1 


# Time
def get_cat21(df):
    # 1: month 
    # 2: day of the month
    # 3: day of the week
    # 4: hour of the day
    # 5: minute of the hour
    # 6: second of the minute
    time = np.full([df.shape[0],6], np.nan)
    time[:,0] = df['mddate'].str[-5:-3].astype(int)
    time[:,1] = df['mddate'].str[-2:].astype(int)
    time[:,2] = pd.to_datetime(df['mddate']).dt.weekday
    time[:,3] = df['mdtime'].astype(str).str[:-7].astype(int)
    time[:,4] = df['mdtime'].astype(str).str[-7:-4].astype(int)
    time[:,5] = df['mdtime'].astype(str).str[-4:].astype(int)
    
    df1 = pd.DataFrame(time,columns=['month','day_of_month','day_of_week','hour_of_day', 'minute','second'])
    return df1 
    
    
    
由于实盘计算脚本名称变更，目前已知需要调整的文件有：
ddb.cfg： startup


    

