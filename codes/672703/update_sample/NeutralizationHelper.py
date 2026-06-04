import numpy as np
import pandas as pd
import os
from Normalization import Normalization
from sklearn.linear_model import LinearRegression

def fillna_to_industry_avg(group):
    return group.fillna(group.mean())

def Raw_Factor_Fill_Na(RawFactor, is_valid_raw, industry_code_all):
    
    tmp = pd.concat([is_valid_raw.reindex(RawFactor.index).stack(dropna=False),
                 industry_code_all.reindex(RawFactor.index).stack(dropna=False),
                 RawFactor.stack(dropna=False)],axis=1).reset_index()
    tmp.columns = ['date', 'stock', 'is_valid_raw','industry_code_all', 'RawFactor']
    tmp = tmp[tmp['is_valid_raw'].values == 1]
    new = tmp[['date', 'industry_code_all','RawFactor']].groupby(['date', 'industry_code_all']).transform(fillna_to_industry_avg)
    tmp['RawFactor'] = new
    tmp = tmp.pivot(index = 'date', columns ='stock', values = 'RawFactor')
    NewFactor = pd.DataFrame(np.nan, index = RawFactor.index, columns=is_valid_raw.columns)
    NewFactor.loc[tmp.index, tmp.columns] = tmp.values
    return NewFactor

def Update_Industry_Size_Neu_Factors(factor_name, RawFactor, NormSize,IndustryMark,is_valid_raw,industry_code_all, DatesNeedUpdate):
    
    if RawFactor.index[-1] != NormSize.index[-1]:
        print(factor_name, RawFactor.index[-1], NormSize.index[-1])
        assert False, 'Factor date is not consistent with size factor date'
        
    if RawFactor.index[0] != NormSize.index[0]:
        print(factor_name, RawFactor.index[0], NormSize.index[0])
        assert False, 'Factor date is not consistent with size factor date'
        
    RawFactor_fillna = Raw_Factor_Fill_Na(RawFactor, is_valid_raw, industry_code_all)
    NormFactor=Normalization(RawFactor_fillna)
    NormFactor=NormFactor.norm_dataframe() 
    
    NeutralizedFactor = []

    for date in DatesNeedUpdate:

        RawFactorCurDate = NormFactor.loc[date]
        RawFactorCurDate.name = 'RawFactor'
        NormSizeCurDate = NormSize.loc[date]
        IndustryMarkCurDate = IndustryMark.xs(date, level=1).transpose()

        PreparedData = pd.concat([RawFactorCurDate, NormSizeCurDate, IndustryMarkCurDate],axis =1).dropna()
        if len(PreparedData) == 0:
            RawFactorSeries = pd.Series(np.nan, index = RawFactorCurDate.index, name= date)
            NeutralizedFactor.append(RawFactorSeries)
            continue

        reg=LinearRegression(fit_intercept=False, n_jobs= 1)
        X = PreparedData.drop(['RawFactor'],axis=1).values
        y = PreparedData.transpose().loc[['RawFactor']].values.T
        reg.fit(X, y)
        residual = y-reg.predict(X)
        NeutralizedFactorSeries = pd.Series(np.nan, index = RawFactorCurDate.index, name= date)
        NeutralizedFactorSeries.loc[PreparedData.index] = residual.T[0]
        NeutralizedFactor.append(NeutralizedFactorSeries)

    NeutralizedFactorDf = pd.concat(NeutralizedFactor,axis=1).transpose()
    return NeutralizedFactorDf


def Get_Industry_Mark_And_Size(TeamDataCenterPath, StartDate):

    IndustryCodes = pd.read_pickle(TeamDataCenterPath +'/Basic/daily/industry_code_all.pkl')[StartDate:]
    IndustryList = IndustryCodes.stack().unique()
    IndustryList = IndustryList[IndustryList!=0]

    Size = pd.read_pickle(TeamDataCenterPath+ '/Basic/daily/mkt_cap_ard.pkl') [StartDate:]
    Size = np.log(Size)

    if IndustryCodes.index[-1] != Size.index[-1]:
        assert False,  'Industry code date is not consistent with size factor date'
    
    IndustryMark = {}
    for industry in IndustryList:
        tmp = pd.DataFrame(0., index = IndustryCodes.index, columns=IndustryCodes.columns)
        tmp[IndustryCodes.values == industry] = 1
        IndustryMark[(industry)] = tmp
    IndustryMarkDf = pd.concat(IndustryMark)

    NormSize=Normalization(Size,axis=0)
    NormSize=NormSize.norm_dataframe() 

    return IndustryMarkDf, NormSize
    
    
def Update_Neutraized_Factor_To_Newest(factor_name, industrymark, normsize,is_valid_raw,industry_code_all, IndustrySizeNeutralizedPath, DataCenterFactorPath, StartDate):
    print(factor_name)
    if os.path.exists(IndustrySizeNeutralizedPath + factor_name + '.pkl'):

        neutralized_factors = pd.read_pickle(IndustrySizeNeutralizedPath + factor_name +'.pkl').loc[:StartDate]
        raw_factor = pd.read_pickle(DataCenterFactorPath + factor_name +'.pkl').loc[StartDate:]
        # normsize = normsize.loc[StartDate:]
        # industrymark = industrymark.loc[StartDate:]
        # is_valid_raw = is_valid_raw.loc[StartDate:]
        # industry_code_all = industry_code_all.loc[StartDate:]
        dates_need_update = list(set(raw_factor.index.tolist())-set(neutralized_factors.index.tolist()))
        if len(dates_need_update) == 0:
            print("%15s  is already up-to-date: %12s" % (factor_name, neutralized_factors.index[-1].strftime('%Y-%m-%d')))

        else:
            print("%15s start update from: %12s, update %d days" % (factor_name, StartDate,len(dates_need_update)))
            normsize,industrymark,is_valid_raw,industry_code_all
            update_neutralized_factors = Update_Industry_Size_Neu_Factors(factor_name, raw_factor, normsize,industrymark,is_valid_raw,industry_code_all, dates_need_update)

            neutralized_factors_new = neutralized_factors.append(update_neutralized_factors)
            neutralized_factors_new = neutralized_factors_new.loc[~neutralized_factors_new.index.duplicated(keep='last')].sort_index()
   
            neutralized_factors_new.to_pickle(IndustrySizeNeutralizedPath + factor_name + '.pkl')
    else:
        # If Neutralized Factor doesnt exist, go through every date in history, and save result data frame

        raw_factor = pd.read_pickle(DataCenterFactorPath + factor_name +'.pkl')[StartDate:]
        dates_need_update = raw_factor.index.tolist() 
        
        print("%15s never exists, generate from: %12s, update %d days" % (factor_name, raw_factor.index[0].strftime('%Y-%m-%d'),len(dates_need_update)))
        update_neutralized_factors = Update_Industry_Size_Neu_Factors(factor_name, raw_factor, normsize, industrymark,is_valid_raw,industry_code_all,dates_need_update)
        
        neutralized_factors_new = update_neutralized_factors
        neutralized_factors_new = neutralized_factors_new.sort_index()
        neutralized_factors_new.to_pickle(IndustrySizeNeutralizedPath + factor_name + '.pkl')
    
