import pandas as pd
import numpy as np
import time
import os
import datetime
import multiprocessing
from Normalization import Normalization
import NeutralizationHelper as neuhelper
from sklearn.externals.joblib import Parallel,delayed
Basic_Path =  '/data/group/800020/AlphaDataCenter/Basic/daily/'
Minute_Path = '/data/group/800020/AlphaDataCenter/Basic/minute/'
TeamDataCenterPath = '/data/group/800020/AlphaDataCenter/'
DataCenterFactorPath = '/data/group/800020/AlphaDataCenter/Factor/daily/'
Sample_Raw_Path = '/data/group/800020/AlphaDataCenter/Sample/RawSample/'
Sample_Norm_Path = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'
IndustrySizeNeutralizedPath = '/data/group/800020/AlphaDataCenter/NeutralizedFactors/IndustrySizeNeutralized/'
def Update_Sample(date_need_update, future_return_df, latest_date, Basic_Path, 
            Industry_Size_Neutralized_Path, Sample_Raw_Path, Sample_Norm_Path):
    
    t = time.time()
    print('start updating sample ', date_need_update)
    future_return_df = future_return_df[future_return_df['date'] == date_need_update]
    date_need_update = pd.to_datetime(date_need_update)
    
    is_valid = pd.read_pickle(Basic_Path+'is_valid.pkl').reindex([date_need_update])
    is_valid_raw = pd.read_pickle(Basic_Path+'is_valid_raw.pkl')
    assert is_valid_raw.index[-1] >= latest_date, 'is_valid_raw is not updated!'
    industry_code_all = pd.read_pickle(Basic_Path+'industry_code_all.pkl')
    assert industry_code_all.index[-1] >= latest_date, 'industry_code_all is not updated!'


    is_valid['date'] = is_valid.index
    is_valid_m = is_valid.melt(id_vars= 'date',var_name='stock', value_name='is_valid')

    is_valid_raw['date'] = is_valid_raw.index
    is_valid_raw_m = is_valid_raw.melt(id_vars= 'date',var_name='stock', value_name='is_valid_raw')

    industry_code_all['date'] = industry_code_all.index
    industry_code_all_m = industry_code_all.melt(id_vars='date', var_name = 'stock',value_name='industry_id')

    all_samples = is_valid_m.merge(is_valid_raw_m, on =['stock','date'], how = 'left')
    all_samples = all_samples.merge(future_return_df,on =['stock','date'], how = 'left')
    all_samples = all_samples.merge(industry_code_all_m,on =['stock','date'], how = 'left')

    for factor_name in AllFactorNames:
        factor = pd.read_pickle(Industry_Size_Neutralized_Path +factor_name+'.pkl')
        factor = factor.reindex([date_need_update])
        factor['date'] = factor.index
        tmp = factor.melt(id_vars='date')
        tmp.columns = ['date','stock',factor_name]
        all_samples = all_samples.merge(tmp, on=['date','stock'], how = 'left')


    all_samples.to_pickle(Sample_Raw_Path + date_need_update.strftime('%Y%m%d') +'.pkl')
    print('finish updating sample ', date_need_update, time.time()-t)
    

    all_samples = all_samples[all_samples['is_valid']==1]
    tmp = all_samples[AllFactorNames +['industry_id']].groupby('industry_id')
    all_samples[AllFactorNames] = tmp.transform(fillna_to_industry_avg)
    all_labels= future_return_df.columns[2:].tolist()
    NORM = Normalization(all_samples[AllFactorNames + all_labels], weight=5, axis=1)
    
    all_samples_norm = NORM.norm_dataframe()
    all_samples_norm['stock'] = all_samples['stock']
    all_samples_norm['date'] = all_samples['date']
    all_samples_norm['industry_id'] = all_samples['industry_id']
    all_samples_norm = all_samples_norm.fillna(0)
    
    all_samples_norm.to_pickle(Sample_Norm_Path + date_need_update.strftime('%Y%m%d') +'.pkl')

    return
    
    
def fillna_to_industry_avg(group):
    return group.fillna(group.mean())
def generate_price(date=None,price_type='vwap'):
    '''
    price_type:全天价格包括vwap,close,open
    minute 价格形势：以开始时间点和结束时间点，如'0930:0959'，表示9:30到10点之前的价格均价
    ## 如果取分钟时间点，取一样的时间点即可,如'0930:0930'表示9:30分这一分钟的价格
    '''
    if date is None:
        assert False,'input sample date'
    all_day_price = ['vwap','close','open']
    if price_type in all_day_price:
        price = pd.read_pickle(Basic_Path+'/'+price_type+'_adj.pkl')
        price = price.loc[date]
    else:
        hour = ['09','10','11','13','14']
        assert len(price_type)==9 and price_type[4]=='_','minute price_type error'
        assert (price_type[:2] in hour) and (price_type[5:7] in hour),'minute price_type hour wrong'
        assert (int(price_type[2:4])>=0) and (int(price_type[2:4])<=59) and (int(price_type[7:])>=0) and (int(price_type[7:])<=59),'minute price_type minute wrong'
        assert ((int(price_type[:4])>=930) and (int(price_type[:4])<=1129)) or ((int(price_type[:4])>=1300) and (int(price_type[:4])<=1459)),'minute price_type wrong range'
        assert ((int(price_type[5:])>=930) and (int(price_type[5:])<=1129)) or ((int(price_type[5:])>=1300) and (int(price_type[5:])<=1459)),'minute price_type wrong range'
        assert int(price_type[:4])<=int(price_type[5:]),'begin_time is later than end_time'
        price = {}
        adj = pd.read_pickle(Basic_Path+'adjfactor.pkl')
        begin_time,end_time = price_type.split('_')
        for dt in date:
            volume = pd.read_pickle(Minute_Path+'/Volume/'+dt.strftime("%Y%m%d")+'.pkl')
            amt = pd.read_pickle(Minute_Path+'/Amount/'+dt.strftime("%Y%m%d")+'.pkl')
            begin_t = pd.Timestamp(dt.strftime("%Y%m%d")+begin_time+'00')
            end_t = pd.Timestamp(dt.strftime("%Y%m%d")+end_time+'00')
            price_today = pd.Series(np.nan,index=volume.columns)
            volume_sum = volume.loc[begin_t:end_t].sum(axis=0)
            if (volume_sum>0).sum()>0:
                price_today = amt.loc[begin_t:end_t].sum(axis=0)/volume_sum
                price_today[np.isinf(price_today)] = np.nan ## 只有出现price_today全为np.nan时才会报错
            price[dt] = price_today
        price = pd.DataFrame(price).T.sort_index()
        price = price*adj.loc[date]
    return price      
def get_future_return(Basic_Path):
    price_type_list=['vwap','0930_1129','1300_1429']
    lag_list = [1,3,5]
    industry_code_all =  pd.read_pickle(Basic_Path+'industry_code_all.pkl')[StartDate:]
    assert industry_code_all.index[-1] >= latest_date, 'industry_code_all is not updated!'
    date_list = industry_code_all.index.tolist()
    future_return_df = industry_code_all.stack(dropna=False).to_frame(name='industry_code_all')
    ori_label_list = []
    for t in price_type_list:
        vwap_adj = generate_price(date_list,t)
        for lag in lag_list:
            vwap_re = vwap_adj.pct_change(lag).shift(-(lag+1))
            label = t+'_re_'+str(lag)+'d'
            ori_label_list.append(label)
            future_return_df[label] = vwap_re.stack(dropna=False)
    future_return_df = future_return_df.reset_index().rename(columns={'level_0':'date','level_1':'stock'})
    for l in ori_label_list:
        future_return_df['industry_'+l] = future_return_df[['date','industry_code_all',l]].dropna().groupby(['date','industry_code_all']).transform(lambda x:x-x.mean())
    return future_return_df
        
StartDate = '20200110'
num_process = 24
AllFactorNames = ['ACD6d', 'ACDIndicator', 'AbsRet2Deal', 'AgainstBeta', 'AmPmDiff', 'AmtEhdReverse', 'AmtRet1d', 'AmtRet20d', 'AmtRet5d', 'AmtRet60d', 'AmtStd20d', 'AmtStd60d', 'AmtStdBias', 'AmtStdMean20d', 'AmtStdMean60d', 'AmtVolStdRankMean5d', 'Amt_MidP_Diff', 'Argmin5d', 'AroonDown5d', 'Atr10d', 'Atr20d', 'Atr50d', 'Atr5d', 'Atr60d', 'AtrDelta10d20d', 'AtrDelta10d50d', 'AtrDelta20d50d', 'AtrDelta20d60d', 'AtrDelta5d10d', 'AtrRetCorr', 'AvgTurn20d', 'AvgTurn60d', 'BR20d', 'Bias120d', 'Bias30d', 'BollingerDown20d', 'BollingerUp20d', 'BotTopCumSwingStdRatio', 'CCAREnhancedPVCorr', 'CCAREnhancedPVCorrMean20d', 'CCI10d', 'CCI60d', 'CEMVsharpe', 'CEMVstd', 'CSTurnpureCorrRet', 'CSTurnpureCorrRetSharp', 'CdABReversion', 'CdASReversion', 'CloseCorrTurnR2', 'CloseDistance2Journey', 'CloseLoc', 'ClosePercent2Journey', 'ClosePercentDeal5d_up', 'ClosePercentHighLow', 'ClosePercentIndus', 'ClosePercentLast60', 'ClosePercentRank10d_up', 'ClosePercentRank5d', 'ClosePercentSharpe5d', 'ClosePercentUp5d', 'CloseTurnCorr', 'CloseVolatility', 'CloseVolatility5d', 'CloseVwapRetKurt', 'CloseVwapRetSkew', 'CorrCloseTurn10d', 'CorrCloseTurn10d_max', 'CorrCloseTurn20d_max', 'CorrCloseTurn5d', 'CorrCloseTurn5d_max', 'CorrCloseVolumeSharpe', 'CorrDownVolumeSharpe', 'CorrVolReturn5d', 'Coskew60d', 'CybzCorrClose', 'DavisWin', 'DealnumSharpe', 'DeltaCloseAdj10d', 'DeltaCloseAdj1d', 'DeltaCloseAdj20d', 'DeltaCloseAdj5d', 'DeltaCloseAdj60d', 'DeltaTo5DMin', 'DeltaTurn', 'DeltaTurnSkew', 'DeltaVolume', 'DeltaVwapAdjValid', 'DownDayReturn', 'DownSpace', 'DownUpMeanRatio5d', 'DownUpSumRatio5d', 'DownVolRatioDiff30', 'DownVolatility120d', 'DownVolatility20d', 'DownVolatility5d', 'DownVolatility60d', 'DuoKongMix', 'DuoKongPV', 'DuoKongVar', 'DuoKongVolumeVar', 'EBITDev', 'EMVA', 'EP_Hist1_5D', 'EP_Hist2_120D', 'EbitTTM', 'EbitdaTTM', 'EodMove', 'ExcessRetVolatility', 'FR10d_1001', 'FR10d_1130', 'FR20d_1001', 'FR20d_1130', 'FR40d', 'FR40d_1001', 'FR40d_1130', 'FallTurnover', 'GTJA_001', 'GTJA_002', 'GTJA_003', 'GTJA_004', 'GTJA_005', 'GTJA_006', 'GTJA_007', 'GTJA_008', 'GTJA_009', 'GTJA_011', 'GTJA_012', 'GTJA_013', 'GTJA_014', 'GTJA_015', 'GTJA_016', 'GTJA_017', 'GTJA_018', 'GTJA_019', 'GTJA_020', 'GTJA_021', 'GTJA_022', 'GTJA_025', 'GTJA_026', 'GTJA_027', 'GTJA_028', 'GTJA_029', 'GTJA_031', 'GTJA_032', 'GTJA_033', 'GTJA_034', 'GTJA_035', 'GTJA_036', 'GTJA_037', 'GTJA_038', 'GTJA_039', 'GTJA_040', 'GTJA_041', 'GTJA_042', 'GTJA_045', 'GTJA_048', 'GTJA_052', 'GTJA_053', 'GTJA_054', 'GTJA_056', 'GTJA_057', 'GTJA_058', 'GTJA_059', 'GTJA_060', 'GTJA_061', 'GTJA_062', 'GTJA_063', 'GTJA_064', 'GTJA_065', 'GTJA_066', 'GTJA_067', 'GTJA_068', 'GTJA_069', 'GTJA_070', 'GTJA_071', 'GTJA_072', 'GTJA_073', 'GTJA_074', 'GTJA_076', 'GTJA_077', 'GTJA_078', 'GTJA_079', 'GTJA_080', 'GTJA_081', 'GTJA_082', 'GTJA_083', 'GTJA_084', 'GTJA_085', 'GTJA_087', 'GTJA_090', 'GTJA_091', 'GTJA_092', 'GTJA_093', 'GTJA_094', 'GTJA_095', 'GTJA_096', 'GTJA_097', 'GTJA_098', 'GTJA_099', 'GTJA_105', 'GTJA_115', 'GTJA_118', 'GTJA_121', 'GTJA_124', 'GTJA_176', 'GTJA_179', 'GTJA_223', 'GTJA_224', 'GrahamGrowth', 'GrahamValue', 'GrowthRefined', 'HS300CorrClose', 'HighLowStdRatio5d', 'HighLowStdRatio_mean20d', 'HighLowSwingRatio', 'HighLowVwapRatio5d', 'HighTurnCorr', 'HighVolCorrStd', 'HighVolumeCorr10d', 'IdeaReverser5d', 'IlliqCv20d', 'IlliqCv60d', 'IlliqMean2TurnoverStd', 'IlliqNeg20d', 'IlliqNeg60d', 'IlliqSwing', 'IndustryNeutralizedTurnoverStd', 'LargeSmallVolumeVWAPRatio', 'Last15MinTrendStrength5d', 'Last30MinRetDownVol5d', 'Last30MinUpDownMoneyRatio5d', 'Last30MinsVwapCloseRatio5d', 'Last30MinutesLongShortRatio1d', 'LiqCorr', 'LiqRatio', 'LiqRatio5d', 'LiqRatioAS', 'LiqRatioSA', 'LiqRatioStd', 'LongBear', 'LongBull', 'LongShortPower', 'LowCandleBottom', 'LowSharpeAmountStdRatio', 'LowWire', 'MDI', 'MPV_EWMA', 'MPV_EWMAHHI', 'MPV_EWMASTD', 'MTM20d', 'MTM5d', 'Max2Min5d', 'MeanTurn2RetDown5d', 'MidPVolCorr20', 'Min10VolBurst5Wegihted5d', 'Min10mRetUpVar', 'Min15DPVbias', 'Min15DPVcorr', 'Min15mPriceMax', 'Min15mPricePath', 'Min30CEMVbias', 'Min30CEMVsharpe', 'Min30RSRS', 'Min30WeightVolAmpCloseRatio', 'Min30_PRchange_1d', 'Min30_PRchange_5d', 'Min30_PVchange_1d', 'Min5LastHalfHourRVI', 'Min5LastHalfHourVR', 'Min5LastHalfHourVR5dCut', 'Min5LastHalfHourVRSI10d', 'Min5LastHalfHourVolStd5d', 'Min5LastHourElder20d', 'Min5LastHourElder5dSharp', 'Min5LastHourMFI5d', 'Min5LastHourVwapCorrVolume10dSharp', 'Min5LastHourVwapCorrVolume5d', 'Min5LongShortRatioCut5d', 'Min5VwapToClose20d', 'Min5mAmtRatio', 'Min5mTopVolRet', 'Min60RSRS', 'Min60UpDownRatio', 'Min60_RVstd', 'MinAbnCorr', 'MinAmtMidChg', 'MinAmtMidSkew', 'MinAmtMidStd', 'MinCEMVskew', 'MinCloseCallAmt30maCorr', 'MinCloseCallAmt5maCorr', 'MinCloseCallAmt5maCorrSharpe', 'MinCloseCallAmtBias5d', 'MinCloseCallAmtHHI5d', 'MinCloseCallAmtRatio', 'MinCloseReSkew5d', 'MinCloseVolume', 'MinCloseVolumeRank', 'MinCorHighVolumeMax10d', 'MinCorrRank', 'MinCorrRankMean', 'MinCorrRto5m5dAdj', 'MinCorrVolumePrice', 'MinCorrVolumePrice10d', 'MinCorrVolumePrice20d', 'MinCorrVolumeRetUp10d', 'MinCorrVolumeRetUp5d', 'MinDirectedVol', 'MinDownPVCorr', 'MinEMVA', 'MinEMVAsharpe', 'MinEMVAstd', 'MinExcessIndusPercent', 'MinExcessSharpe', 'MinExcessSharpe5d', 'MinHighCorrVolume3d', 'MinHighVolRet', 'MinHighVolSwing', 'MinHighVolumeRankCorr20d', 'MinIdx300Corr', 'MinIdx500Corr', 'MinIndexCorr', 'MinLowToHighUpPower', 'MinMaxDrawDownUp', 'MinNoiseReverse', 'MinPMAmpVolume5d', 'MinPMSignAmplitude5d', 'MinPmRSRS', 'MinPmRSRS5d', 'MinRRC', 'MinRST', 'MinRSTstd', 'MinReboundRate5d', 'MinRetRange', 'MinReturnVolUp2Down5d', 'MinSignedAmtMaxDrawdown', 'MinSignedAmtPriceDelayDeltaCorr', 'MinSignedAmtPriceDelayDeltaCorrMean', 'MinSkew20d', 'MinSkewSharpe10d', 'MinSkewStd20d', 'MinSkipCorrRatio', 'MinSmartFoolRatio', 'MinSmartFoolRatioMean', 'MinTMcorr', 'MinTVolStd', 'MinTWAPExcessSharpe10d', 'MinTWAPReSharpe5d', 'MinTopRetUpVar', 'MinTopVolCorr5D', 'MinTopVolRate', 'MinUpBackSharpe', 'MinUpBackStd', 'MinUpDownMean2Vol5d', 'MinUpDownRatio', 'MinUpDownRetAcc', 'MinUpVoteRatio', 'MinVRCExcess5d', 'MinVVCorrRank', 'MinVVCorrRankStd', 'MinVVRankCorrStd', 'MinVVRtoCorrRank', 'MinVVRtoCorrRankMean', 'MinVolAmpCorrRatio', 'MinVolWeightedRet5d', 'MinVolumeVolUp2Down5d', 'MinVwapRV', 'MinVwapRV5', 'MinVwapRV5skew', 'MinVwapRVskew', 'MinWR_20_80', 'MinWeightVolReRatio', 'MinWeightVolReSkew', 'MinWeightVolReSwing', 'Min_ACD', 'Min_ACDBias', 'Min_ACDSharp', 'Min_ACDZScore', 'Min_AR', 'Min_CloseAutoCorrZScore', 'Min_CloseBias', 'Min_CloseBuySellStrength', 'Min_CloseBuySellStrengthZScore', 'Min_CloseSignAutoCorr', 'Min_CloseSignAutoCorrZScore', 'Min_CorrCloseVolume', 'Min_CorrReturnVolume', 'Min_DownReturn', 'Min_IlliqCloseReturn', 'Min_IlliqShortcut', 'Min_OCVR20d', 'Min_OverBuy', 'Min_OverBuyVol', 'Min_PredictReturn2Volume', 'Min_PredictReturnMean', 'Min_PredictReturnSharp', 'Min_PredictReturnZScore', 'Min_RSRS', 'Min_Range_Ratio_1d', 'Min_Range_Ratio_20d', 'Min_Range_Ratio_5d', 'Min_RelativeDownReturn', 'Min_TurnoverSharp', 'Min_TurnoverStd', 'Min_UpRange', 'Minute15mReTo5D', 'Minute30m5dTurnStd', 'Minute30m5dVolumeHHI', 'Minute5dAmtSimilarityRet', 'Minute60minBias5d', 'MinuteALTKurt', 'MinuteAbnormalRe5d', 'MinuteAbnormalRe5m', 'MinuteAfterRAVwapReturn5d', 'MinuteAmPmReturnDiff', 'MinuteAmtAutocorr5d', 'MinuteAmtCV3d', 'MinuteAmtCV5d', 'MinuteAmtRetCor1d', 'MinuteAmtRetCor5d', 'MinuteAmtStdSwing', 'MinuteAroon', 'MinuteBias30m5D', 'MinuteCloseAmtReHHI', 'MinuteCloseAmtReMean', 'MinuteCloseAmtReVote', 'MinuteCloseCallAuctionTurnover', 'MinuteCloseConsistency', 'MinuteCloseDiff', 'MinuteCloseDuoKong', 'MinuteCloseMMT', 'MinuteCloseMomentumBias', 'MinuteCloseMomentumSharpe', 'MinuteCloseNetural', 'MinuteCloseOpenEWMA', 'MinuteClosePriceXCorr', 'MinuteCloseRDailyR', 'MinuteCloseResist', 'MinuteCloseSmartGame', 'MinuteCloseTurn', 'MinuteCloseTurnCorr', 'MinuteCloseTurnPlus', 'MinuteCloseTurnRank', 'MinuteCloseTurnRev', 'MinuteCloseTurnSharp', 'MinuteCloseTurnoverStd', 'MinuteCloseUpVar', 'MinuteCloseVol30mChg', 'MinuteCloseVolumeXCorr', 'MinuteCloseWR', 'MinuteCloseWREWMA', 'MinuteCloseWRVolume', 'MinuteClosingSREWM', 'MinuteClosingSessionVolumePercent', 'MinuteCorrCloseVolume', 'MinuteCorrPriceNotional', 'MinuteCorrPriceNotionalSharpe', 'MinuteCorrPriceVolumeSharpe', 'MinuteCorrRank', 'MinuteCorrReturnVolumeResampled', 'MinuteCorrVWAPVolume', 'MinuteCorrVolVwap', 'MinuteDCDTA', 'MinuteDCDTA5d', 'MinuteDailyMtm', 'MinuteDownVolatilityRatio20d', 'MinuteDuoKong0', 'MinuteEODRetDrawdownRatio', 'MinuteEODRetDrawdownRatioSharpe', 'MinuteEODRetVolMultiple', 'MinuteEODRetVolMultipleBias', 'MinuteEODReturn', 'MinuteEODSharpe', 'MinuteEODSkewness120Min', 'MinuteEODSortinoRatio', 'MinuteEODSortinoRatioSharpe', 'MinuteEODVolWeightedLongShortPower', 'MinuteEODVolWeightedLongShortPowerSharpe', 'MinuteEODVolumeRatio', 'MinuteEODVolumeWeightedReturn', 'MinuteEODVolumeWeightedReturnEWM', 'MinuteEODVolumeWeightedReturnSharpe', 'MinuteEODWinRate', 'MinuteGroupReBias5d', 'MinuteHTRtnRvs', 'MinuteHighPricePos5d', 'MinuteIdioKurt5d', 'MinuteIdioSkew5d', 'MinuteIlliqLast30m5D', 'MinuteIlliqVwapClose5d', 'MinuteLHourSkew', 'MinuteLTSkew', 'MinuteLast15Volume', 'MinuteLast1hrSkewSharpe', 'MinuteLast1hrSkewSharpeBias', 'MinuteLast30mPriceVolRefine', 'MinuteLast30mPriceVolRefineHHI', 'MinuteLast30mPriceVolRefineMean', 'MinuteLast3hrsSkewSharpe', 'MinuteLast60mLongVolRatio', 'MinuteLastHourMDDMCLIMB20d', 'MinuteLastHourMDDMCLIMBstd20d', 'MinuteLastHourMaxClimb20dSR', 'MinuteLastHourMtm', 'MinuteLastHourPVCorr', 'MinuteLastHourSkewness5d', 'MinuteLastHrCorrPriceNotional', 'MinuteLastMtmRank5d', 'MinuteLastMtmRankVote5d', 'MinuteLastPSY', 'MinuteLastReStd1D', 'MinuteLastRetCMO', 'MinuteLastSR5HHI', 'MinuteLastSR5d', 'MinuteLastTurn20std', 'MinuteLastVolumeRank5std', 'MinuteLastVwapVolumeCorr', 'MinuteLongBear', 'MinuteMADistance', 'MinuteMADistanceMA', 'MinuteMADistanceSP', 'MinuteMPVCorrRank', 'MinuteMacdEma10d', 'MinuteMaxDistanceRetMA', 'MinuteMaxTenMinReturn', 'MinuteMaxTenMinReturnSharpe', 'MinuteMovingAverageDiffMax', 'MinuteMovingAverageDiffMaxEWM', 'MinutePCorr', 'MinutePMRtnZscore10d', 'MinutePVCorr', 'MinutePVCorrMean', 'MinutePVCorrMin', 'MinutePVCorrMinAdj', 'MinutePVCorrStdAdj', 'MinutePmSkew', 'MinutePmSkewEma10d', 'MinutePmSkewSharpe', 'MinutePmTrendStr', 'MinutePosNegVolumeRatio', 'MinutePriceMACD', 'MinutePriceStd10d', 'MinuteRAVolumeRatio5d', 'MinuteRSIVolume', 'MinuteRSRSResidVolatilityZscore5d', 'MinuteRSRSstd5d', 'MinuteRTC', 'MinuteRePerDeal5d', 'MinuteRelativeUpVar', 'MinuteRetLastHrSkew', 'MinuteRetSkewnessSharpe', 'MinuteRetTurnCorr', 'MinuteRetTurnRho', 'MinuteRetVolMultMean', 'MinuteRetVolMultSharpe', 'MinuteRetVolMultSkew', 'MinuteRetVolMultSkewSharpe', 'MinuteRetVolProdSkew', 'MinuteRetVolProdSkewSharpe', 'MinuteReturnAutocorr5d', 'MinuteReturnDiffStdSharpe', 'MinuteReturnSkew', 'MinuteReturnSkewSharpe', 'MinuteReturnSkewnessSharpe', 'MinuteReturnStdSharpe', 'MinuteReturnVolSharpe', 'MinuteReturnVolumeMultiple', 'MinuteReturnVolumeMultipleSharpe', 'MinuteSignedAbnormalSmartHHI', 'MinuteSignedAbnormalSmartMean', 'MinuteSignedAvgDistanceDiff', 'MinuteSignedAvgDistanceDiffMean', 'MinuteSkew10d', 'MinuteSkew20d', 'MinuteSkew5d', 'MinuteSortinoSharpe', 'MinuteSwing', 'MinuteTAVwapReturn5d', 'MinuteTERtnVRatio', 'MinuteTHLCorrRank', 'MinuteTLSTDiffRatio', 'MinuteTLSTRvs', 'MinuteTLSVRatio', 'MinuteTLTurn', 'MinuteTPVDeltaCorr', 'MinuteTRC', 'MinuteTRtnVGRank', 'MinuteTRtnVGStdRank', 'MinuteTRtnVRatioRank', 'MinuteTRtnZscore', 'MinuteTSD', 'MinuteTTLSStdRank', 'MinuteTTPVCorr', 'MinuteTVRtnRank', 'MinuteTWR', 'MinuteTrendStr', 'MinuteTrendStrSharp', 'MinuteTrendStrength10d', 'MinuteTrendStrength20d', 'MinuteTrendStrength5d', 'MinuteTurnWeightedHLongRe', 'MinuteTurnWeightedHLongReMean', 'MinuteTurnoverStdSharpe', 'MinuteTurnoverVolSharpe', 'MinuteUpVar', 'MinuteVARe5d', 'MinuteVAVwapReturnSR5d', 'MinuteVMASkew', 'MinuteVVCorrHalfRatio', 'MinuteVWAPSharpe', 'MinuteVWAPSortino', 'MinuteVWAPSortinoSharpe', 'MinuteValidRet', 'MinuteVarianceRatio', 'MinuteVirtualHighLowPathSR5d', 'MinuteVirtualHighLowStdDif5d', 'MinuteVirtualHighLowStdSR5d', 'MinuteVirtualLineUpdownAmt5d', 'MinuteVol', 'MinuteVolCV60m5D', 'MinuteVolCVSharpe10d', 'MinuteVolCVSkew10d', 'MinuteVolChgCorr', 'MinuteVolVwapCorrCloseChg', 'MinuteVolWeightedPowerEWM', 'MinuteVolofVolumeHHI', 'MinuteVolume30minHHISharpe', 'MinuteVolumeHHI', 'MinuteVolumeHHISharpe', 'MinuteVolumeKurt', 'MinuteVolumeMACD', 'MinuteVolumeRate', 'MinuteVolumeRatioBias', 'MinuteVolumeSkew', 'MinuteVolumeStabilitySharpe', 'MinuteVolumeStd20dCV', 'MinuteVolumeStdSharpe', 'MinuteVolumeWeightedReturnSharpe', 'MinuteVwapDiff', 'MinuteWRMean', 'MinuteWRVolume', 'MinuteliqAmtRatioSharpe20d', 'MinuteliqSwingSharpe5d', 'MinuteliqSwingStd5', 'MomHigh2Low10d', 'MomHigh2Low20d', 'MomHighExclMorn20d', 'MomHighPm5d', 'NIGrowthZscore1y', 'NI_SQ_IndustryRank', 'NegativeIlliquidity', 'NetProfitSurprise', 'NonstationaryPV', 'NonstationaryPVSharp', 'OpenGapVolSharp10d', 'OpenHighMoveHigher', 'OvernightDaytimeMomentum', 'P2GWin', 'PB_Hist1_250D', 'PB_Hist2_5D', 'PCFWin', 'PDPS_Hist1_120D', 'PDPS_Hist2_120D', 'PEAdj', 'PEWin', 'PSWin', 'PS_Hist1_20D', 'PS_Hist2_250D', 'PVStdCap', 'PVTTurn20d', 'PVTTurn5d', 'PVcorrMom', 'PctChangeMax20d', 'PctChangeMax5d', 'PctChangeMax60d', 'PePercent240d', 'PeRoe', 'PeakDistancePV', 'PmVolumeRatio', 'PredictReturn2Volume', 'PriceBiasDividStd60', 'PriceBiasZscore60', 'PriceChangePmToAm', 'PriceDelay', 'PriceDiff', 'ROEWin', 'ROE_SQ', 'RSI', 'RangeRetCorr20', 'RankNetProfitDps', 'RankPBDev', 'RankPBRel', 'RankPEChange', 'RankPEDev', 'RankPERel', 'RankedReversion', 'Re300ReturnScore5D', 'ReCorr20', 'Relative300Return5D', 'Relative500ReturnEMA10D', 'Relative500ReturnEMA120D', 'Relative500ReturnEMA20D', 'Relative500ReturnEMA60D', 'RelativeDy', 'RelativeIndPE40d', 'RelativeIndPE5d', 'RelativeIndPEAS', 'RelativeIndPEGAvg', 'RelativePB', 'RelativePE', 'RelativePS', 'ResidualReturn500Sharpe', 'RetCorrCloseRank', 'RetCorrTurnDelay', 'RetCorrTurnDelayPure', 'RetCutCorrTurnDelay', 'RetVolumeRetMultSharpe', 'ReturnSkewEMA20d', 'ReverseDistance', 'ReverseMomentum', 'ReverseMomentumDouble', 'ReverseMomentumTriple', 'ReversePV40d', 'RhoCloseAmtMa20d', 'RhoCloseAmtMa60d', 'RhoSwingAmt20d', 'RhoSwingAmt60d', 'RoeNeuPb', 'SPPI', 'SectorIlliquidity', 'SectorNotionalSharpe', 'SectorOverperformanceVol', 'SectorPESharpe', 'SectorSize', 'SectorSkewness', 'ShortBear', 'ShortBull', 'SignedPriceRatio', 'SimpleVolume', 'SizeNeuTurn5d', 'StdMaxAmountRatio', 'SwingDays10d', 'SwingDays20d', 'SwingDays5d', 'SwingDownUpRatio', 'SwingHighLowPriceCorr', 'SwingToTurn', 'SwingTurn', 'TopAmountRatioVolumeDiffSharpe', 'TurnAmtCorr20d', 'TurnCV20', 'TurnCorrSharp', 'TurnDays10d', 'TurnDays20d', 'TurnDays5d', 'TurnDays60d', 'TurnMidCorr', 'TurnNeuIndusRank', 'TurnNeuRetCorrSharp', 'TurnPE', 'TurnPEAS', 'TurnPEAvg', 'TurnPEStd', 'TurnPercent_1d_240d', 'TurnPriceRatio10d', 'TurnPriceRatio20d', 'TurnRankPercent_1d_240d', 'TurnoverMean2Std', 'TurnoverSharpe', 'TurnoverSharpe100d', 'TurnoverStdRatio', 'Twap2Vwap', 'TyDegree', 'TyVolatility', 'UpDownVol5d', 'UpDownVolatility', 'UpVolDiff30', 'UpVolRatioDiff30', 'UpVolatility120d', 'UpVolatility20d', 'UpVolatility5d', 'UpVolatility60d', 'ValueDelay', 'ValueGrowth', 'ValueRefined', 'VolCV_60D', 'VolPriceCorr', 'VolPriceFlyer', 'VolPriceFlyerPlus', 'VolPriceRunner', 'VolitilityMax', 'VolitilityRelative', 'VolumePriceKurt120d', 'VolumePriceKurt240d', 'VolumePriceKurt60d', 'VolumeRatio20d', 'VolumeRatio5d', 'VolumeRatio60d', 'VolumeRatioDown20d', 'VolumeReversionMultiple', 'VolumeShortLongStdRatio', 'VolumeStdBias', 'VoteDiff30', 'VwapCloseAdj20d', 'VwapTurnStdRatio', 'Vwap_Close_Range_Diff', 'WAPResistBackRatio', 'WAPResistBackStd', 'WAPResistBackTop', 'WQ_004', 'WQ_011', 'WQ_015', 'WQ_026', 'WQ_027', 'WQ_035', 'WQ_038', 'WQ_042', 'WQ_044', 'WQ_054', 'WeightedDownUpSumRatio5d', 'ZZ500CorrClose', 'ZaoYinTrader', 'alpha12', 'alpha53', 'netprofit_std']
is_valid = pd.read_pickle(Basic_Path+'is_valid.pkl')[StartDate:]
latest_date = is_valid.index[-1]
print(' ####################  Latest date is ', latest_date.strftime('%Y-%m-%d'), ' ###############')
industry_code_all = pd.read_pickle(Basic_Path + 'industry_code_all.pkl')[StartDate:]
is_valid_raw = pd.read_pickle(Basic_Path + 'is_valid_raw.pkl')[StartDate:]

industrymark, normsize = neuhelper.Get_Industry_Mark_And_Size(TeamDataCenterPath, StartDate)


Parallel(n_jobs=num_process)(delayed(neuhelper.Update_Neutraized_Factor_To_Newest)(f,industrymark,normsize, 
                                                                                    is_valid_raw,
                                                                                    industry_code_all,
                                                                                    IndustrySizeNeutralizedPath, 
                                                                                    DataCenterFactorPath,
                                                                                    StartDate) for f in AllFactorNames)      


print('*******************  Tech Factors  Finished ******************************\n')

DataCenterFactorPath = '/data/group/800020/AlphaDataCenter/Factor/fundamental_tmp/'
AllFactorNames = sorted(e[:-4] for e in os.listdir(DataCenterFactorPath))

Parallel(n_jobs=num_process)(delayed(neuhelper.Update_Neutraized_Factor_To_Newest)(f,industrymark,normsize, 
                                                                                    is_valid_raw,
                                                                                    industry_code_all,
                                                                                    IndustrySizeNeutralizedPath, 
                                                                                    DataCenterFactorPath,
                                                                                    StartDate) for f in AllFactorNames) 

print('*******************  Fundamental Factors  Finished ******************************\n')

  

AllFactorNames = sorted(e[:-4] for e in os.listdir(IndustrySizeNeutralizedPath))
StartDate = '20200110'

for factor in AllFactorNames:
    factor_lastdate = pd.read_pickle(IndustrySizeNeutralizedPath+ factor + '.pkl').index[-1]
    assert factor_lastdate >= latest_date, factor +' is not updated!'
    
hist_dates = sorted(os.listdir(Sample_Raw_Path))
all_dates = sorted([e.strftime('%Y%m%d') for e in is_valid.index])

if len(hist_dates)> 50:
    dates_not_need_update = hist_dates[:-50]
    dates_need_update = [e for e in all_dates if e >dates_not_need_update[-1]] 
else:
    dates_not_need_update = []
    dates_need_update = all_dates


future_return_df = get_future_return(Basic_Path)

Parallel(n_jobs=num_process)(delayed(Update_Sample)(date_need_update, 
                            future_return_df, 
                            latest_date, 
                            Basic_Path, 
                            IndustrySizeNeutralizedPath, 
                            Sample_Raw_Path,
                            Sample_Norm_Path) for date_need_update in dates_need_update) 
  

