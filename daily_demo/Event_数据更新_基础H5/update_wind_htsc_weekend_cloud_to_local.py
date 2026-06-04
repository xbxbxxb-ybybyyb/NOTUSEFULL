import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import os
from multiprocessing import Pool, Process, Manager
from multifactor.data.utils import *
import logging
from log import Log
import multifactor.utility.dt as tdt
import pickle
from xquant.factordata import FactorData
import time

logger = Log('update_wind_htsc')
s = FactorData()

def get_all_days(sdate,edate):
    h5_path = '/data/group/800080/warehouse/prod/CALENDAR/nature_days.h5'
    df = IO.read_data([sdate,edate],alt=h5_path)
    df.reset_index(inplace=True)
    df['dt'] = df['dt'].apply(lambda x : int(str(x).replace('-','')[:8]))
    date_list = list(set(df['dt']))
    date_list.sort()
    return date_list
class WIND_DATABASE:
    def __init__(self, table_name, sdate, edate, 
                 base_path = '/data/group/800080/warehouse/prod/', 
                 dtype = 'STOCK',
                 mkttype = 'CHINA',
                 ftype = 'FDD',
                 dfreq = 'QUARTERLY',
                 dsource = 'WIND',
                 operation = 'append'):
        
        self.table_name = table_name
        self.sdate = sdate
        self.edate = edate
        self.dtype = dtype
        self.mkttype = mkttype
        self.ftype = ftype
        self.dfreq = dfreq
        self.dsource= dsource
        self.base_path = base_path
        self.source_path = os.path.join(base_path,'LOCAL_DATA/CSV/',dsource)
        self.operation = operation
        current_time = dt.datetime.strftime(dt.datetime.now(),'%Y%m%d')#_%H%M%S')
        self.table_csv_path =  os.path.join(self.source_path,self.table_name)
        name_mapping_dict = {}
        if self.table_name in name_mapping_dict:
            self.h5_name = name_mapping_dict[self.table_name]
        else:
            self.h5_name = self.table_name[5:]
        self.table_h5_path =  os.path.join(self.base_path,'DATABASE/WIND/', self.h5_name)
        self.table_h5_file =  os.path.join(self.table_h5_path,self.h5_name+'.h5')
        for path in [self.table_csv_path,self.table_h5_path]:
            if not os.path.exists(path):
                logger.info('retriever: create folder:%s'%(path))
                os.makedirs(path)
    
        if self.dfreq=='DAILY':
            self.cdate_list = get_all_days(sdate,edate)
            self.cdate_list.sort()   
        elif self.dfreq=='QUARTERLY':
            qtr_list = get_qtr_list(self.sdate,self.edate,num_qtr=3)
            self.cdate_list = qtr_list
        else:
            raise Exception
        self.over_write_list = ['WIND_AShareIndustriesClassCITICS', 'WIND_AShareDescription', 'WIND_AShareIndustriesCode','WIND_AShareST',
                        'WIND_AShareCapitalization', 'WIND_AShareFreeFloat', 'WIND_AShareIPO', 'WIND_AShareAgency',
                         'WIND_AShareCOCapitaloperation', 'WIND_ASharePledgepro', 'WIND_AshareStockRepo', 'WIND_AShareCorporateFinance',
                         'WIND_AShareIssueCommAudit', 'WIND_AShareEquityDivision', 'WIND_AShareStaff',
                         'WIND_IPOCompRFA', 'WIND_IECMemberList', 'WIND_AShareLeadUnderwriter',
                         'WIND_AShareRightIssue', 'WIND_AShareSEO', 'WIND_IPOInquiryDetails',
                         'WIND_AShareManagement', 'WIND_AShareIncDescription', 'WIND_AShareIncQuantityPrice', 'WIND_AShareIncQuantityDetails',
                         'WIND_AShareIncExercisePct', 'WIND_AShareIncExecQtyPri', 'WIND_AShareEsopDescription', 'WIND_AShareEsopTradingInfo',
                         'WIND_AShareStaffStructure', 'WIND_AShareMajorHolderPlanHold','WIND_AShareTypeCode','WIND_htzqedbdzzbs',
                         'WIND_AShareMainandnoteitems','WIND_AIndexMembers','WIND_AShareConseption']  
       
    # different tables - different paremeters - get dataframe
    def get_df(self, date):
        
        print(date)
        
        if self.table_name in ['WIND_AShareFinancialIndicator', 'WIND_AShareProfitExpress', 'WIND_AShareTTMHis',
                          'WIND_AShareBalanceSheet','WIND_AShareCashFlow','WIND_AShareIncome','WIND_CMMFPortfolioPTM',
                        'WIND_AShareinstHolderDerData', 'WIND_AShareIssuingDatePredict', 'WIND_AShareANNFinancialIndicator',
                        'WIND_FinNotesDetail','WIND_AShareIBrokerIndicator','WIND_AShareInsuranceIndicator','WIND_AShareBankIndicator',
                        'WIND_AShareAuditOpinion','WIND_AIndexFinancialderivative','WIND_AShareSalesSegment',
                        'WIND_Top5ByLongTermBorrowing','WIND_Top5ByOperatingIncome','WIND_CBankFinNotes','WIND_AShareFinExpense',
                        'WIND_AshareOthreceivables', 'WIND_Top5ByAccReceivable','WIND_AshareInventorydetails','WIND_AshareFinaccounts',
                        'WIND_AShareDividend']:
            df = s.get_factor_value(self.table_name, report_period=[str(date)])
            
        elif self.table_name in ['WIND_AShareMonthlyReportsofBrokers']:
            df = s.get_factor_value('WIND_AShareMonthlyReportsofBrokers', report_period=[str(date)])

        elif self.table_name in ['WIND_AShareProfitNotice']:
            df = s.get_factor_value(self.table_name, S_ProfitNotice_Period=[str(date)])

        elif self.table_name in ['WIND_AShareEODPrices', 'WIND_AShareEODDerivativeIndicator','WIND_SHSCDailyStatistics',
                            'WIND_SHSCShortselling','WIND_SHSCTop10ActiveStocks','WIND_SHSCChannelholdings',
                            'WIND_AShareMarginTrade', 'WIND_AShareMarginTradeSum', 'WIND_AShareBlockTrade',
                            'WIND_AShareInsiderTrade', 'WIND_AShareMoneyFlow', 'WIND_AShareL2Indicators', 
                            'WIND_AIndexEODPrices', 'WIND_ASharePlacementDetails', 'WIND_ASharePlacementInfo','WIND_AShareTechIndicators',
                            'WIND_AshareintensitytrendADJ', 'WIND_AShareEnergyindexADJ', 'WIND_AShareswingRevADJ',
                            'WIND_AIndexIndustriesEODCITICS','WIND_AIndexValuation','WIND_SIndexPerformance','WIND_AIndexWindIndustriesEOD']:
            df = s.get_factor_value(self.table_name, trade_dt=[str(date)])
        elif self.table_name in ['WIND_CMFundAssetPortfolio', 'WIND_CMFundIndPortfolio', 'WIND_CMFundBondPortfolio']:
            df = s.get_factor_value(self.table_name, F_PRT_ENDDATE=[str(date)])
        elif self.table_name in ['WIND_CMFOtherPortfolio',  'WIND_AShareHolderNumber', 'WIND_AShareIllegality',
                                'WIND_AShareInsideHolder', 'WIND_AShareMjrHolderTrade','WIND_AShareFloatHolder',
                                'WIND_AShareFFCalendar', 'WIND_AShareEquityPledgeInfo','WIND_AShareCompRestricted',
                                'WIND_ASarePlanTrade']:
            df = s.get_factor_value(self.table_name, ANN_DT=[str(date)])
        elif self.table_name in ['WIND_AShareAnnInf']:
            df = s.get_factor_value(self.table_name, ANN_DT=['to_date(' + str(date) + ",'YYYYMMDD')"])
            # pass
            # do something special deal with datetime type 
        elif self.table_name in ['WIND_CMFundStockPortfolio']:
            df = s.get_factor_value(self.table_name, ANN_DATE=[str(date)])
        elif self.table_name in ['WIND_AShareEXRightDivRecord']:
            df = s.get_factor_value(self.table_name, ex_date=[str(date)])
        elif self.table_name in ['WIND_AShareMarginSubject']:
            df = s.get_factor_value(self.table_name, s_margin_effectdate=[str(date)])
        elif self.table_name in ['WIND_AShareMarginShortFeeRate']:
            df = s.get_factor_value(self.table_name, effective_date=[str(date)])
        elif self.table_name in ['WIND_AShareStrangeTradedetail']:
            df = s.get_factor_value(self.table_name, start_dt=[str(date)])
        elif self.table_name in ['WIND_AShareStrangeTrade']:
            df = s.get_factor_value(self.table_name, s_strange_bgdate=[str(date)])
        elif self.table_name in ['WIND_AShareMajorEvent']:
            df = s.get_factor_value(self.table_name, S_EVENT_ANNCEDATE=[str(date)])
        # elif self.table_name in self.over_write_list:
            # sql_where = ''
            # df = s.get_factor_value(self.table_name)
        # elif self.table_name in ['WIND_htzqedbdzzbs']:
        #     sql_where = ' where TDATE='
        elif self.table_name in ['WIND_AShareManagementHoldReward']:
            df = s.get_factor_value(self.table_name, ANN_DATE=[str(date)])
        elif self.table_name in ['WIND_BOIndexWeightsWIND']:
            df = s.get_factor_value(self.table_name, CHANGE_DT=[str(date)])
        elif self.table_name in ['WIND_AShareStyleCoefficient']:
            df = s.get_factor_value(self.table_name, S_CHANGE_DATE=[str(date)])
        elif self.table_name in ['WIND_AShareTradingSuspension']:
            df = s.get_factor_value(self.table_name, S_DQ_SUSPENDDATE=[str(date)])
        else:
            logger.error('retriever: table not defined: %s'%(self.table_name))
            raise Exception
        
        return df

    def retriever(self):
        
        logger.info('retriever: fetch data from %s for %d - %d'%(self.table_name,self.sdate,self.edate))
        logger.info('retriever: data saved in:  %s'%(self.table_csv_path))
        
        # download data - save to csv
        if self.table_name == 'WIND_AShareMonthlyReportsofBrokers':
            _,_,tmp_date_list = check_update_date(sdate = 20040101, edate = self.cdate_list[-1])
            new_cdate_list = []
            month_dict = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
            for date in self.cdate_list:
                year = int(int(date)/10000)
                month = int(int(date) % 10000 / 100)
                if month == 1:
                    year = year - 1
                    month = 12
                else:
                    month -= 1
                if month == 2 and year % 4 == 0:
                    month_date = year * 10000 + month * 100 + 29
                else:
                    month_date = year * 10000 + month * 100 + month_dict[month]
                if not month_date in new_cdate_list:
                    new_cdate_list.append(month_date)
            for date in new_cdate_list:
                sql_use =  str(date)
                # logger.info(sql_use)
                save_name = os.path.join(self.table_csv_path,str(date) + '.csv')
                try:
                    df = s.get_factor_value('WIND_AShareMonthlyReportsofBrokers', report_period=[str(date)])
                    def help(df,tmp_date_list):
                        date = df['ANN_DT']
                        date = int(date)
                        while date not in tmp_date_list and date < tmp_date_list[-1]:
                            date += 1
                        return str(date)
                    df['ANN_DT_modified'] = df.apply(lambda x : help(x,tmp_date_list), axis=1)
                    df.set_index('OBJECT_ID', inplace = True)
                    df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                    logger.info('retriever: saved in :  %s'%(save_name))
                except Exception as err:
                    if len(df) == 0:
                        df.to_csv(save_name, sep=',', encoding='utf_8_sig')

                    logger.warning('%s got exception as follows: '%(self.table_name))
                    print(err)
                
        else: 
            if self.table_name in self.over_write_list:
                try:
                    df = s.get_factor_value(self.table_name)
                    df['date'] = self.cdate_list[-1]
                    save_name = os.path.join(self.table_csv_path,self.table_name + '.csv')
                    df.set_index('OBJECT_ID', inplace = True)
                    df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                    logger.info('retriever: saved in :  %s'%(save_name))
                except Exception as err:
                    logger.warning('%s got exception as follows: '%(self.table_name))
                    print(err)
                    df = s.get_factor_value(self.table_name, OPDATE=['>=20130101']).append(s.get_factor_value(self.table_name, OPDATE=['<20130101']))
                    df['date'] = self.cdate_list[-1]
                    save_name = os.path.join(self.table_csv_path,self.table_name + '.csv')
                    df.set_index('OBJECT_ID', inplace = True)
                    df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                    logger.info('retriever: saved in :  %s'%(save_name))
            else:
                for date in self.cdate_list:
                    try:
                        df = self.get_df(date)
                        save_name = os.path.join(self.table_csv_path,str(date) + '.csv')
                        df.set_index('OBJECT_ID', inplace = True)
                        df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                        logger.info('retriever: saved in :  %s'%(save_name))
                    except Exception as err:
                        logger.warning('%s got exception as follows: '%(self.table_name))
                        print(err)
                    
                    
        logger.info('retriever: %s  done'%(self.table_name))
        return
    
    def dumper(self):
        logger.info('dump_h5: %s, %d, %d, %s, %s, %s'%(self.table_name,self.sdate,self.edate,self.ftype,self.dfreq,self.dsource))
            
        csv_list = [os.path.join(self.table_csv_path,i) for i in os.listdir(self.table_csv_path)]
        # print('@@@@@@@@@@@@@@@')
        # print(csv_list)
        csv_list.sort()
        
        if self.dfreq =='QUARTERLY':
            update_list = [i for i in csv_list if int(i[-12:-4])>=self.sdate-10000 and int(i[-12:-4])<=self.edate and int(i[-12:-4])>=20000101] # update for 1 year
        elif self.dfreq =='DAILY':
            if self.table_name in self.over_write_list:
                update_list = csv_list
            elif self.table_name == 'WIND_AShareMonthlyReportsofBrokers':
                new_cdate_list = []
                update_list = []
                month_dict = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
                for date in self.cdate_list:
                    year = int(int(date)/10000)
                    month = int(int(date) % 10000 / 100)
                    if month == 1:
                        year = year - 1
                        month = 12
                    else:
                        month -= 1
                    if month == 2 and year % 4 == 0:
                        month_date = year * 10000 + month * 100 + 29
                    else:
                        month_date = year * 10000 + month * 100 + month_dict[month]
                    if not month_date in new_cdate_list:
                        new_cdate_list.append(month_date)
                        update_list.append(os.path.join(self.table_csv_path,str(month_date)+'.csv'))
                        print(update_list)
            else:
                # print(csv_list)
                update_list = [i for i in csv_list if int(i[-12:-4])>=self.sdate and int(i[-12:-4])<=self.edate and int(i[-12:-4])>=20000101] 
        self.csv2h5(update_list)
        
        return 

def get_table_param(table_name,table_dict):
    param_dict = {}
    if table_name in table_dict['QUARTERLY']:
        param_dict['dfreq']='QUARTERLY'
    elif table_name in table_dict['DAILY']:
        param_dict['dfreq']='DAILY'
    else: 
        print ('table not defined: %s'%table_name)
        raise Exception   
    return param_dict


def instantiate(table_name, sdate, edate, base_path, operation,table_dict,update_h5_flag=False):
    # get dfreq
    param_dict = get_table_param(table_name,table_dict)
    wind_db = WIND_DATABASE(table_name, sdate, edate, base_path, 
                            dfreq = param_dict['dfreq'],
                            operation = operation)    
    wind_db.retriever()
    # if update_h5_flag:

 
def first_job(sdate=None,edate=None):
  
    qtr_list = ['WIND_AShareBalanceSheet','WIND_AShareCashFlow','WIND_AShareIncome','WIND_AShareProfitExpress',
                'WIND_AShareProfitNotice','WIND_AShareFinancialIndicator','WIND_AShareTTMHis', 'WIND_AShareANNFinancialIndicator', 
                'WIND_AShareIssuingDatePredict','WIND_AShareDividend','WIND_AIndexFinancialderivative']

    qtr_list2 = ['WIND_AShareSalesSegment','WIND_AShareFinExpense','WIND_AShareAuditOpinion',
    'WIND_AShareIBrokerIndicator',
            'WIND_AShareBankIndicator','WIND_AShareInsuranceIndicator']

    daily_list = ['WIND_AShareDescription','WIND_AShareIndustriesClassCITICS','WIND_AShareST', 'WIND_AShareManagement',
                'WIND_AShareMonthlyReportsofBrokers','WIND_AShareManagementHoldReward','WIND_AIndexMembers','WIND_AShareConseption',
                'WIND_AShareRightIssue'] 
    
    daily_list2 = ['WIND_AShareStaff','WIND_AShareIPO','WIND_AShareSEO','WIND_AShareMjrHolderTrade']
    
    
    table_dict = {'QUARTERLY': qtr_list + qtr_list2, 'DAILY': daily_list + daily_list2}

    for table_type in table_dict:
        for table_name in table_dict[table_type]:
            print (table_name)
            instantiate(table_name, sdate, edate, base_path = '/data/user/015623/warehouse/prod/'+str(edate), operation = 'append',table_dict=table_dict)

    logger.info('===============1st job upload finish======================')

def get_current_nature_date(new_date_time=18):
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    print('Current time: ' + str(current_time))
    h5_path = '/data/group/800080/warehouse/prod/CALENDAR/nature_days.h5'
    fdate_list_dt = IO.read_data([19980101, 20210101], alt=h5_path).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x: abs(x - current_date) if x <= current_date else 100)
    if current_hour < new_date_time and nearest_date == current_date:
        print('Not till refresh time ' + str(new_date_time) + ':00')
        current_date = fdate_list[fdate_list.index(current_date) - 1]
        print('Use previous trading date: ' + str(current_date))
    elif nearest_date < current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date == current_date:
        print('Right on time: ' + str(current_date))
    return current_date 
    
    
sdate = get_current_nature_date()
edate = sdate
print(sdate)
first_job(sdate,sdate)

import os
if not os.path.exists('/data/user/015623/zip_wind/' + str(edate)):
    os.makedirs('/data/user/015623/zip_wind/' + str(edate))
os.system('zip -r /data/user/015623/zip_wind/' + str(edate) + '/' + str(edate) + '.zip /data/user/015623/warehouse/prod/' + str(edate) + '/LOCAL_DATA/CSV/WIND/')
from xquant.pyfile.ftp import pyfileFTP
ftp = pyfileFTP()
ftp.uploadDir("/data/user/015623/zip_wind/"+str(edate), "015623/zip_wind/" + str(edate) )