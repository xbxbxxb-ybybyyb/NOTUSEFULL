import pandas as pd 
import datetime
import time 
from xquant.compute.aimr import AIMR
import sys 
sys.path.insert(0,'update_factor/')
from update_factor_exector import *
argus = pd.read_pickle(update_factor_help_path+'start_end_date.pkl')
#argus={'start_date':'20210101','end_date':'20210110'}
today = datetime.date.today().strftime('%Y%m%d')
#today='20210917'
t0= time.time()

if(not 'start_date' in argus.keys()):
    argus['start_date']=today
if(not 'end_date' in argus.keys()):
    argus['end_date']=today
if(type(argus['start_date'])==int):
    argus['start_date']=str(argus['start_date'])
if(type(argus['end_date'])==int):
    argus['end_date']=str(argus['end_date'])
t0=time.time()
catalog_type=['daily']
multi_flag = True
for t in catalog_type:
    if not os.path.exists(factor_data_path+t+'/'):
        os.makedirs(factor_data_path+t+'/')
    factor_list=catalog_factor(factor_management_path,'.json',t)
#    this_factor_list = ['TyHelp', 'MinCloseCallAmtRatio', 'Atr20d', 'Atr5d', 'Atr10d', 'Atr50d', 'Atr60d', 'MinuteLast30mPriceVolRefine', 'AtrDelta10d20d', 'MPV_EWMASTD', 'CCAREnhancedPVCorrMean20d', 'AtrDelta5d10d', 'AtrDelta10d50d', 'MPV_EWMAHHI', 'TyVolatility', 'AtrDelta20d50d', 'MPV_EWMA', 'AtrDelta20d60d', 'TyDegree', 'CCAREnhancedPVCorr']
    this_factor_list = ['AvgTurn60d', 'CSTurnpureCorrRet', 'CSTurnpureCorrRetSharp', 'CdABReversion', 'CloseDistance2Journey', 'CloseTurnCorr', 'CorrCloseTurn5d_max', 'CorrCloseVolumeSharpe', 'DownUpSumRatio5d', 'DownVolatility20d', 'EodMove', 'FR10d_1130', 'GTJA_005', 'GTJA_006', 'GTJA_015', 'GTJA_042', 'GTJA_054', 'GTJA_057', 'GTJA_059', 'GTJA_068', 'GTJA_073', 'GTJA_076', 'GTJA_085', 'GTJA_223', 'IdeaReverser5d', 'IlliqMean2TurnoverStd', 'LongBull', 'Min30RSRS', 'Min30_PRchange_5d', 'Min5LastHalfHourRVI', 'Min5LastHalfHourVR', 'Min5LastHalfHourVR5dCut', 'Min5LastHalfHourVolStd5d', 'Min5LastHourMFI5d', 'MinAmtMidSkew', 'MinCEMVskew', 'MinEMVA', 'MinRST', 'MinSignedAmtPriceDelayDeltaCorr', 'MinSkewStd20d', 'MinVRCExcess5d', 'MinVwapRVskew', 'Min_IlliqCloseReturn', 'Min_IlliqShortcut', 'Min_OverBuy', 'Min_TurnoverSharp', 'Minute30m5dVolumeHHI', 'Minute60minBias5d', 'MinuteALTKurt', 'MinuteAroon', 'MinuteCloseTurnSharp', 'MinuteClosingSessionVolumePercent', 'MinuteDuoKong0', 'MinuteEODRetDrawdownRatioSharpe', 'MinuteEODReturn', 'MinuteEODWinRate', 'MinuteIdioSkew5d', 'MinuteLastRetCMO', 'MinuteLastSR5HHI', 'MinuteMADistance', 'MinutePVCorrMean', 'MinutePriceStd10d', 'MinuteRAVolumeRatio5d', 'MinuteRetTurnRho', 'MinuteRetVolMultSharpe', 'MinuteRetVolProdSkewSharpe', 'MinuteTTPVCorr', 'MinuteTrendStrength5d', 'MinuteTurnWeightedHLongReMean', 'MinuteTurnoverStdSharpe', 'MinuteVARe5d', 'MinuteVolCVSharpe10d', 'MinuteVolWeightedPowerEWM', 'MinuteVolumeMACD', 'NonstationaryPVSharp', 'PDPS_Hist1_120D', 'PePercent240d', 'RankPBDev', 'RankPERel', 'RelativeIndPEGAvg', 'RhoSwingAmt60d', 'SectorOverperformanceVol', 'SimpleVolume', 'SwingDays20d', 'SwingToTurn', 'TurnDays20d', 'VolumeRatio60d', 'ZaoYinTrader']
    factor_list = sorted(list(set(factor_list)&set(this_factor_list)))
    print(len(factor_list),' nums factor is updating ',argus['start_date'],argus['end_date'])
  
    update_factor(factor_list,argus['start_date'], argus['end_date'],multi_flag)
    success_update_factors,fail_update_factors = check_factor_update_success(factor_list,t,argus['start_date'],argus['end_date']) 
    print("update "+t+" finished,cost "+str(time.time()-t0)+" s")
    print(str(len(fail_update_factors))+' factor updated fail.')
    print(str(fail_update_factors)+' updated fail.')
print('cost time',time.time()-t0)

change_permission(factor_data_path)
