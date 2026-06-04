import time
import numpy as np
import pandas as pd
import copy
from sklearn.linear_model import LinearRegression
from sklearn.externals.joblib import Parallel,delayed
import multiprocessing
import warnings
warnings.simplefilter(action = "ignore", category = RuntimeWarning)
num_threads=20
class Neutralize(object):
    '''
      data is DataFrame,how is MultiIndex,index all is stock list
    '''
    def  __init__(self,data,how=None):
        self.how = copy.deepcopy(how)
        if isinstance(data,pd.DataFrame):
            data = data.stack(dropna=False)
        self.how.insert(0,'test',data)
    def neutralize(self):
        res = self.how.groupby(level=0).apply(self.neutralize_help)
        del self.how
        return res
    def neutralize_help(self,factor_data):
        resid = pd.Series(index=factor_data.index.levels[1])
        prepared_neu = factor_data.dropna()
        if(len(prepared_neu)==0):
            return resid
        need_index = prepared_neu.index.remove_unused_levels().levels[1]
        model=LinearRegression(fit_intercept=False,n_jobs=num_threads)
        X = prepared_neu.iloc[:,1:].values
        y = prepared_neu.iloc[:,0].values
        model.fit(X,y)
        resid.loc[need_index] = y-model.predict(X)
        return resid

class Winsorize(object):
    """
    class to remove extreme 
    """
    def __init__(self,data,scale=None,method='std',qrange=None,vrange=None,inclusive=True,
                 inf2nan=True,axis=1):
        assert ~((scale is None) |(qrange is None) | (vrange is None)),'scale,range,qrange,3 select 1'
        self.data = data
        self.data= self.data.astype(np.float64)
        self.scale = scale
        self.method = method
        self.vrange = vrange
        self.qrange = qrange
        self.inclusive = inclusive
        self.axis = axis
        if inf2nan == True:
            self.data[np.isinf(self.data)] = np.nan
    def winsorize(self):
        if not self.scale is None:
            return self.data.apply(lambda x:self.scale_remove_extreme(x),axis=self.axis)
        elif not((self.qrange is None) | (self.vrange is None)):
            return self.data.apply(lambda x:self.range_remove_extreme(x),axis=self.axis)
        else:
            raise NotImplementedError("this winsorize method is not supported yet")      
    def range_remove_extreme(self,arr):
        if not self.qrange is None:
            q = arr.quantile([min,max])
            arr = np.clip(arr,q[0],q[1])
        else:
            arr = np.clip(arr,min,max)
        return arr
    def scale_remove_extreme(self,arr):
        """
        arr is a one-dimensinal vector, remove extreme by mad method
        """
        diversion = len(np.unique(arr[~np.isnan(arr)]))/(~np.isnan(arr)).sum()
        
        if diversion>0.1 and ~np.isinf(diversion):
            md = np.nanmedian(arr)
            mad = np.nanmedian(np.abs(arr[arr!=md] - md))
            upper = md + self.scale*mad
            lower = md - self.scale*mad
            if self.method == 'std':
                mu = np.nanmean(arr)
                sigma = np.nanstd(arr,ddof=1)
                upper = mu + self.scale*sigma
                lower = mu - self.scale*sigma
            extreme_count  = ((arr>upper)|(arr<lower)).sum()
            nan_count = (~np.isnan(arr)).sum()
            if (extreme_count>nan_count*0.1)&(extreme_count<=nan_count*0.2):
                upper = md + (self.scale+1)*mad
                lower = md - (self.scale+1)*mad

            elif(extreme_count>nan_count*0.2):
                upper = md + (self.scale+2)*mad
                lower = md - (self.scale+2)*mad
            if self.inclusive == True:
                arr[arr>upper] = upper
                arr[arr<lower] = lower
            else:
                arr[arr>upper] = np.nan
                arr[arr<lower] = np.nan
        return arr
        

class Standardlize(object):
    """
    class to stardardize 
    """
    def __init__(self,data,method="zscore",inf2nan=True,axis=1):
        self.data = data
        self.data= self.data.astype(np.float64)
        if inf2nan==True:
            self.data[np.isinf(self.data)] = np.nan
        self.method = method
        self.axis = axis
    
    def standardlize(self):
        """
        """
        if self.method=='zscore':
            return self.data.apply(lambda x:self.zscore_stardardize(x),axis=self.axis)
        elif self.method=='maxmin':
            return self.data.apply(lambda x:self.maxmin_stardardize(x),axis=self.axis)
        elif self.method=="L1":
            return self.data.apply(lambda x:self.norm_L1_stardardize(x),axis=self.axis)
        elif self.method=="L2":
            return self.data.apply(lambda x:self.norm_L2_stardardize(x),axis=self.axis)
        elif self.method=="tanh":
            return self.data.apply(lambda x:self.tanh_stardardize(x),axis=self.axis)
        else:
            raise NotImplementedError("this stardardize method is not supported yet")
    
    def zscore_stardardize(self,arr):
        """
        stardardize by zscore method
        """
        if len(arr[~np.isnan(arr)]):
            mu = np.nanmean(arr)
            sigma = np.nanstd(arr,ddof=1)
            if sigma==0:
                return arr
            else:
                arr = (arr - mu) / sigma         
        return arr

    def maxmin_stardardize(self,arr):
        """
        by (max - min)
        """       
        if len(arr[~np.isnan(arr)]):
            max_value = np.nanmax(arr)
            min_value = np.nanmin(arr)
            if max_value==min_value:
                return arr
            else:
                arr = (arr - min_value) / (max_value - min_value)
        return arr

    def norm_L1_stardardize(self,arr):
        """
        stardardize by L1 norm
        """        
        if len(arr[~np.isnan(arr)]):
            l1 = np.nansum(np.abs(arr))
            if l1==0:
                return arr
            else:
                arr = arr / l1              
        return arr

    def norm_L2_stardardize(self,arr):
        """
        stardardize by L2 norm
        """        
        if len(arr[~np.isnan(arr)]):
            l2 = np.sqrt(np.nansum(arr**2))
            if l2==0:
                return arr
            else:
                arr = arr / l2                
        return arr

    def tanh_stardardize(self,arr):
        """
        stardardize by tanh transformation
        """
        if len(arr[~np.isnan(arr)]):
            arr = np.tanh(arr)
        return arr
def winsorize(data, scale=5, method='mad',qrange=None, vrange=None, inclusive=True, inf2nan=True, axis=1):
    return Winsorize(data,scale,method,qrange,vrange,inclusive,inf2nan,axis).winsorize()
def standardlize(data,method="zscore",inf2nan=True, axis=1):
    return Standardlize(data,method,inf2nan,axis).standardlize()
def standard_winsor(data,axis=1):
    return standardlize(winsorize(data,axis=axis),axis=axis)
def apply_parallel(dfGrouped, func):
    retLst = Parallel(n_jobs=num_threads)(delayed(func)(group,axis=0) for name, group in dfGrouped)
    return pd.concat(retLst)
def neu_help(x,how):
    return Neutralize(x,how).neutralize().stack(dropna=False)
# neutralize(data[factor_list],data[neu_basic.columns],data_norm=factor_list,how_norm=['log_mkt'])    
def neutralize(data,how,data_norm=None,how_norm=None):
    if data_norm is None:
        data_norm = data.columns
    if how_norm is None:
        how_norm = how.columns
    data = apply_parallel(data[data_norm].groupby(level=0),standard_winsor)
    feature_list = data.columns
    how = apply_parallel(how[how_norm].groupby(level=0),standard_winsor)
    data = pd.concat(Parallel(n_jobs=num_threads)(delayed(neu_help)(data[x],how) for x in feature_list),axis=1)
    data.columns = feature_list
    return data