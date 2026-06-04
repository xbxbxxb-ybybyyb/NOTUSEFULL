"""
update wind_db from htsc matlab

"""


import datetime as dt
import pandas as pd
import scipy.io as sio
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import sys
from multiprocessing import Pool, Process, Manager
from multifactor.data.utils import *
import logging
from log import Log
import multifactor.utility.dt as tdt
import datetime

logger = Log('update_wind_htsc')

class WIND_DATABASE:
    def __init__(self, table_name, sdate, edate,
                 # modify 修改路径
                 # base_path='Z:\\warehouse\\prod\\',
                 base_path = '/app/data/wdb_h5/',
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
        # modify 修改路径(base_path, 'LOCAL_DATA\\CSV\\', dsource) 为(base_path , dsource)
        self.source_path = os.path.join(base_path ,dsource)
        self.operation = operation
        current_time = dt.datetime.strftime(dt.datetime.now(),'%Y%m%d')#_%H%M%S')
        # modify csv文件与h5文件放进同一文件夹
        self.table_csv_path =  os.path.join(self.source_path,self.table_name[5:])
        name_mapping_dict = {'WIND_AShareAFIndicator': 'AShareANNFinancialIndicator', 'WIND_Ashareeoddindicator': 'AShareEODDerivativeIndicator',
                    'WIND_ASharePledgepro':  'ASharePledgeproportion','WIND_AShareFFCalendar': 'AShareFreeFloatCalendar',
                    'WIND_CMFundAssetPortfolio': 'ChinaMutualFundAssetPortfolio','WIND_CMFundIndPortfolio': 'ChinaMutualFundIndPortfolio',
                    'WIND_CMFundStockPortfolio': 'ChinaMutualFundStockPortfolio', 'WIND_CMFundBondPortfolio': 'ChinaMutualFundBondPortfolio',
                    'WIND_AShareIndClassCITICS': 'AShareIndustriesClassCITICS', 'WIND_AShareMgHoldReward': 'AShareManagementHoldReward', 
                    'WIND_AShareEXRightDivRecord': 'AShareEXRightDividendRecord', 'WIND_AShareswingRevADJ':'AShareswingReversetrendADJ'}
        if self.table_name in name_mapping_dict:
            self.h5_name = name_mapping_dict[self.table_name]
        else:
            self.h5_name = self.table_name[5:]
        print(self.h5_name)
        # modify 修改路径'DATABASE\\WIND\\' 为'WIND\\'
        self.table_h5_path =  os.path.join(self.base_path,'WIND', self.h5_name)
        print(self.table_h5_path)
        self.table_h5_file =  os.path.join(self.table_h5_path,self.h5_name+'.h5')
        print(self.table_h5_file)
        for path in [self.table_csv_path,self.table_h5_path]:
            if not os.path.exists(path):
                logger.info('retriever: create folder:%s'%(path))
                os.makedirs(path)
    
        if self.dfreq=='DAILY':
            self.cdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in tdt.get_trading_date_range(self.sdate,self.edate)]
        elif self.dfreq=='QUARTERLY':
            qtr_list = get_qtr_list(self.sdate,self.edate,num_qtr=3)
            # qtr_list = [i for i in qtr_list if i>20090101]
            self.cdate_list = qtr_list
        else:
            raise Exception
        self.over_write_list = ['WIND_AShareIndClassCITICS', 'WIND_AShareDescription', 'WIND_AShareIndustriesCode','WIND_AShareST',
                        'WIND_AShareCapitalization', 'WIND_AShareFreeFloat', 'WIND_AShareIPO', 'WIND_AShareAgency',
                         'WIND_AShareCOCapitaloperation', 'WIND_ASharePledgepro', 'WIND_AshareStockRepo', 'WIND_AShareCorporateFinance',
                         'WIND_AShareIssueCommAudit', 'WIND_AShareEquityDivision', 'WIND_AShareMgHoldReward', 'WIND_AShareStaff',
                         'WIND_IPOCompRFA', 'WIND_IECMemberList', 'WIND_AShareLeadUnderwriter','WIND_AShareDividend',
                         'WIND_AShareRightIssue', 'WIND_AShareSEO', 'WIND_AShareCompRestricted', 'WIND_IPOInquiryDetails',
                         'WIND_AShareManagement', 'WIND_AShareIncDescription', 'WIND_AShareIncQuantityPrice', 'WIND_AShareIncQuantityDetails',
                         'WIND_AShareIncExercisePct', 'WIND_AShareIncExecQtyPri', 'WIND_AShareEsopDescription', 'WIND_AShareEsopTradingInfo',
                         'WIND_AShareStaffStructure', 'WIND_AShareMajorHolderPlanHold']    
    

    def csv2h5(self, update_list, min_size=0):
        """
            operation = 'append': for existing one - if operation =='append' - will remove existing one 
            operation = 'create': remove completely 
            Removed by type_dropna
            sorted by type_sort - e.g. sorted by entry time
            for removing duplicate - just drop last row for subgroup 
        """
        dat_fig_dict = {'WIND_AShareProfitExpress':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareFinancialIndicator':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareProfitNotice':{'dt':'S_PROFITNOTICE_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareTTMHis':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareEODPrices':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_Ashareeoddindicator':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_SHSCDailyStatistics':{'dt':'TRADE_DT','Ticker':'S_INFO_EXCHMARKET'},
                        'WIND_SHSCTop10ActiveStocks':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_SHSCShortselling':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_SHSCChannelholdings':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareBalanceSheet':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareCashFlow':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareIncome':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_CMMFPortfolioPTM':{'dt':'REPORT_PERIOD','Ticker':'F_INFO_WINDCODE'},
                        'WIND_CMFundAssetPortfolio':{'dt':'F_PRT_ENDDATE','Ticker':'S_INFO_WINDCODE'},
                        'WIND_CMFOtherPortfolio':{'dt':'ANN_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_CMFundIndPortfolio':{'dt':'F_PRT_ENDDATE','Ticker':'S_INFO_WINDCODE'},
                        'WIND_CMFundStockPortfolio':{'dt':'ANN_DATE','Ticker':'S_INFO_WINDCODE'},
                        'WIND_CMFundBondPortfolio':{'dt':'F_PRT_ENDDATE','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareMarginTrade':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareMarginTradeSum':{'dt':'TRADE_DT'},
                        'WIND_AShareMarginSubject':{'dt':'S_MARGIN_EFFECTDATE','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareMarginShortFeeRate':{'dt':'EFFECTIVE_DATE'},
                        'WIND_AShareBlockTrade':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareStrangeTradedetail':{'dt':'START_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareStrangeTrade':{'dt':'S_STRANGE_BGDATE','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareHolderNumber':{'dt':'ANN_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareInsideHolder':{'dt':'ANN_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareFloatHolder':{'dt':'ANN_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareMjrHolderTrade':{'dt':'ANN_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareInsiderTrade':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareMajorHolderPlanHold':{'dt':'date','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareinstHolderDerData':{'dt':'REPORT_PERIOD','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareMoneyFlow':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareL2Indicators':{'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_ASharePledgepro':{'dt':'date','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareFFCalendar':{'dt':'ANN_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareIssuingDatePredict':{'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareAFIndicator':{'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIndClassCITICS':{'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareDescription':{'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIndustriesCode':{'dt': 'date'},
                        'WIND_AIndexEODPrices': {'dt':'TRADE_DT','Ticker':'S_INFO_WINDCODE'},
                        'WIND_AShareST': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCapitalization' : {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareFreeFloat': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIPO': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareAgency': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCOCapitaloperation': {'dt': 'date', 'Ticker': 'S_INFO_COMPCODE'},
                        'WIND_AshareStockRepo': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCorporateFinance': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIssueCommAudit': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEquityDivision': {'dt': 'date', 'Ticker': 'WINDCODE'},
                        'WIND_AShareMgHoldReward': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStaff': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_IPOCompRFA': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_IECMemberList': {'dt': 'date'},
                        'WIND_AShareLeadUnderwriter':{'dt': 'date'},
                        'WIND_AShareDividend': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareRightIssue': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareSEO': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEXRightDivRecord': {'dt': 'EX_DATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCompRestricted': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_ASharePlacementDetails': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_ASharePlacementInfo': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_IPOInquiryDetails': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareManagement': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncDescription': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncQuantityPrice': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncQuantityDetails': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncExercisePct': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncExecQtyPri': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEsopDescription': {'dt': 'date', 'Ticker' : 'S_INFO_WINDCODE'},
                        'WIND_AShareEsopTradingInfo': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStaffStructure': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareTechIndicators': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AshareintensitytrendADJ': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEnergyindexADJ': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareswingRevADJ': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
        
                        }
        #modify dat_fig_dict选一个表测试
        # dat_fig_dict = {'WIND_AShareEODPrices': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'}}
        sparse_list = ['WIND_SHSCDailyStatistics','WIND_SHSCTop10ActiveStocks','WIND_SHSCShortselling','WIND_SHSCChannelholdings']

        logger.info('csv2h5: %s'%(self.table_name))
        dat_fig = dat_fig_dict[self.table_name]
        update_list.sort()

        if self.operation=='create':
            logger.info('csv2h5: create -  %s'%(self.table_h5_file))
            os.remove(self.table_h5_file) if os.path.exists(self.table_h5_file) else None
        elif self.operation == 'append':
            logger.info('csv2h5: append -  %s'%(self.table_h5_file))
    

        if self.table_name in self.over_write_list:
            logger.info('csv2h5: create -  %s'%(self.table_h5_file))
            os.remove(self.table_h5_file) if os.path.exists(self.table_h5_file) else None

        with pd.HDFStore(self.table_h5_file) as h5_store:
            logger.info('csv2h5: check date list')     
            if self.table_name in list(h5_store.root._v_groups.keys()):
                dt_lst = list(set(h5_store.select_column(self.table_name, 'dt')))
            else:
                dt_lst = [] 
            for fname in update_list:
                logger.info(fname)
                dat1 = pd.read_csv(fname, encoding='utf_8_sig')
                if len(dat1)<=min_size:
                    if self.table_name in sparse_list:
                        logger.warning('csv2h5: sparse table %s - data too little '%(self.table_name))
                        pass
                    else:
                        logger.error('csv2h5: source data %s too little!'%(self.table_name))
                        pass
                else:
                    if self.table_name == 'WIND_AShareMarginShortFeeRate':
                        dat1['PUBLISHER_ID'] = dat1['PUBLISHER_ID'].astype(str)
                    dat = data_reformat(dat1, dat_fig)
                    if self.operation == 'append':      
                        curr_date = list(set(dat.index.get_level_values('dt')))[0]
                        print (curr_date)
                        if curr_date in dt_lst:
                            logger.info('csv2h5: exist: %s'%(curr_date))
                            # print('pass')
                            # continue
                            dummy_id = h5_store.remove(self.table_name,'dt=curr_date')
                            logger.info('csv2h5: append: %s'%(curr_date))
                    if self.table_name == 'WIND_AShareProfitNotice':
                        dat.drop(['S_PROFITNOTICE_ABSTRACT'], axis=1, inplace=True)
                        h5_store.append(self.table_name,dat,data_columns=True)
                    elif self.table_name == 'WIND_SHSCDailyStatistics':
                        h5_store.append(self.table_name,dat,data_columns=True,  min_itemsize={'Ticker':10})
                    elif self.table_name == 'WIND_SHSCChannelholdings':
                        h5_store.append(self.table_name,dat,data_columns=True,  min_itemsize={'S_INFO_EXCHMARKETNAME':10})
                    elif self.table_name == 'WIND_SHSCTop10ActiveStocks':
                        h5_store.append(self.table_name,dat,data_columns=True,  min_itemsize={'MARKET':10,'S_INFO_EXCHMARKETNAME':10})
                    elif self.table_name == 'WIND_CMFOtherPortfolio':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype('object')
                        h5_store.append(self.table_name,dat,data_columns=True,  min_itemsize={'Ticker':15, 'S_INFO_HOLDWINDCODE':15})
                    elif self.table_name == 'WIND_CMFundStockPortfolio':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype('object')
                        h5_store.append(self.table_name,dat,data_columns=True,  min_itemsize={'Ticker':15})
                    elif self.table_name == 'WIND_CMFundBondPortfolio':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype('object')
                        dat['S_INFO_BONDWINDCODE'] = dat['S_INFO_BONDWINDCODE'].astype('object')
                        h5_store.append(self.table_name,dat,data_columns=True,min_itemsize={'S_INFO_BONDWINDCODE':15})
                    elif self.table_name == 'WIND_AShareMarginSubject':
                        h5_store.append(self.table_name,dat,data_columns=True,min_itemsize={'Ticker':15})
                    elif self.table_name == 'WIND_AShareMarginShortFeeRate':
                        h5_store.append(self.table_name,dat,data_columns=True)
                    elif self.table_name == 'WIND_AShareBlockTrade':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_BLOCK_SELLERNAME': 150, 'S_BLOCK_BUYERNAME': 150})
                    elif self.table_name == 'WIND_AShareStrangeTrade':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_STRANGE_TRADERNAME': 150})
                    elif self.table_name == 'WIND_AShareInsideHolder':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_HOLDER_MEMO': 750, 'S_HOLDER_NAME': 100, 'S_HOLDER_ANAME':100})
                    elif self.table_name == 'WIND_AShareFloatHolder':
                        dat['S_HOLDER_WINDNAME'] = dat['S_HOLDER_WINDNAME'].astype('object')
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_HOLDER_NAME': 175, 'S_HOLDER_WINDNAME' : 175})
                    elif self.table_name == 'WIND_AShareMjrHolderTrade':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'HOLDER_NAME': 100})                    
                    elif self.table_name == 'WIND_AShareInsiderTrade':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'RELATED_MANAGER_POST': 100, 'RELATED_MANAGER_NAME':100, 'REPORTED_TRADER_NAME' :150, 
                                                                                          'TRADER_MANAGER_RELATION' : 150})
                    elif self.table_name == 'WIND_AShareinstHolderDerData':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_HOLDER_NAME': 120})

                    elif self.table_name == 'WIND_AShareIssuingDatePredict':
                        dat.drop(['S_STM_CORRECT_ISSUINGDATE'], axis=1, inplace=True)
                        h5_store.append(self.table_name,dat,data_columns=True)
                    elif self.table_name == 'WIND_AShareAFIndicator':
                        dat.drop(['MEMO', 'S_INFO_DIV'], axis=1, inplace=True)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_INFO_COMPCODE': 15})
                    elif self.table_name == 'WIND_AShareEXRightDivRecord':
                        dat['EX_TYPE'] = dat['EX_TYPE'].astype('object')
                    elif self.table_name == 'WIND_ASharePlacementDetails':
                        dat['S_HOLDER_NAME'] = dat['S_HOLDER_NAME'].astype('object')
                        dat['TYPEOFINVESTOR'] = dat['TYPEOFINVESTOR'].astype('object')
                        dat['S_HOLDER_TYPE'] = dat['S_HOLDER_TYPE'].astype('object')
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'S_HOLDER_NAME': 200, 'TYPEOFINVESTOR': 50, 'S_HOLDER_TYPE': 75})
                    elif self.table_name == 'WIND_AIndexEODPrices':
                        h5_store.append(self.table_name,dat,data_columns=True, min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_AShareProfitExpress':
                        dat.drop(['BRIEF_PERFORMANCE', 'MEMO'], axis = 1, inplace=True)
                        h5_store.append(self.table_name,dat,data_columns=True)

                    elif self.table_name == 'WIND_AShareBalanceSheet':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name,dat,data_columns=True)

                    elif self.table_name == 'WIND_AShareCashFlow':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name,dat,data_columns=True)

                    elif self.table_name == 'WIND_AShareIncome':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name,dat,data_columns=True)

                    elif self.table_name == 'WIND_AShareTTMHis':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name,dat,data_columns=True)

                    elif self.table_name == 'WIND_AShareFinancialIndicator':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name,dat,data_columns=True)
   
                    elif self.table_name == 'WIND_AshareintensitytrendADJ':
                        h5_store.append(self.table_name,dat,data_columns=True,min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_AShareEnergyindexADJ':
                        h5_store.append(self.table_name,dat,data_columns=True,min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_AShareswingRevADJ':
                        h5_store.append(self.table_name,dat,data_columns=True,min_itemsize={'Ticker': 15})

                    else:
                        h5_store.append(self.table_name,dat,data_columns=True)
    
                    logger.info('csv2h5: %s done'%(fname))
    
        logger.info('csv2h5 all done: %s'%(self.table_name))     
        return 
    
    
    
    def retriever(self):
        #  download table and save it to the csv file
        logger.info('retriever: fetch data from %s for %d - %d'%(self.table_name,self.sdate,self.edate))
        logger.info('retriever: data saved in:  %s'%(self.table_csv_path))
        # add condition
        if self.table_name in ['WIND_AShareFinancialIndicator', 'WIND_AShareProfitExpress', 'WIND_AShareTTMHis',
                          'WIND_AShareBalanceSheet','WIND_AShareCashFlow','WIND_AShareIncome','WIND_CMMFPortfolioPTM',
                        'WIND_AShareinstHolderDerData', 'WIND_AShareIssuingDatePredict', 'WIND_AShareAFIndicator']:
            sql_where = ' where report_period='

        elif self.table_name in ['WIND_AShareProfitNotice']:
            sql_where = ' where S_ProfitNotice_Period='

        elif self.table_name in ['WIND_AShareEODPrices', 'WIND_Ashareeoddindicator','WIND_SHSCDailyStatistics',
                            'WIND_SHSCShortselling','WIND_SHSCTop10ActiveStocks','WIND_SHSCChannelholdings',
                            'WIND_AShareMarginTrade', 'WIND_AShareMarginTradeSum', 'WIND_AShareBlockTrade',
                            'WIND_AShareInsiderTrade', 'WIND_AShareMoneyFlow', 'WIND_AShareL2Indicators',
                            'WIND_AIndexEODPrices', 'WIND_ASharePlacementDetails', 'WIND_ASharePlacementInfo','WIND_AShareTechIndicators',
                            'WIND_AshareintensitytrendADJ', 'WIND_AShareEnergyindexADJ', 'WIND_AShareswingRevADJ']:
        # modify 选择一个表测试
        #elif self.table_name in ['WIND_AShareEODPrices']:
            sql_where = ' where trade_dt=';         
        elif self.table_name in ['WIND_CMFundAssetPortfolio', 'WIND_CMFundIndPortfolio', 'WIND_CMFundBondPortfolio']:
            sql_where = ' where F_PRT_ENDDATE='
        elif self.table_name in ['WIND_CMFOtherPortfolio',  'WIND_AShareHolderNumber',
                                'WIND_AShareInsideHolder', 'WIND_AShareMjrHolderTrade','WIND_AShareFloatHolder',
                                'WIND_AShareFFCalendar', 'WIND_AShareEquityPledgeInfo']:
            sql_where = ' where ANN_DT='
        elif self.table_name in ['WIND_CMFundStockPortfolio']:
            sql_where = ' where ANN_DATE='
        elif self.table_name in ['WIND_AShareEXRightDivRecord']:
            sql_where = ' where ex_date='
        elif self.table_name in ['WIND_AShareMarginSubject']:
            sql_where = ' where s_margin_effectdate='
        elif self.table_name in ['WIND_AShareMarginShortFeeRate']:
            sql_where = ' where effective_date='
        elif self.table_name in ['WIND_AShareStrangeTradedetail']:
            sql_where = ' where start_dt='
        elif self.table_name in ['WIND_AShareStrangeTrade']:
            sql_where = ' where s_strange_bgdate='
        elif self.table_name in self.over_write_list:
            sql_where = ''
        else:
            logger.error('retriever: table not defined: %s'%(self.table_name))
            raise Exception
        # 由于Oracle标识符长度限制，无法创建对应的同义词，所以使用别名
        table_alias = {
            'WIND_AIndexEODPrices': 'WIND.AIndexEODPrices',
            'WIND_AShareAgency': 'WIND.AShareAgency',
            'WIND_AShareBlockTrade': 'WIND.ASHAREBLOCKTRADE',
            'WIND_AShareCapitalization': 'WIND.AShareCapitalization',
            'WIND_AShareCOCapitaloperation': 'WIND.AShareCOCapitaloperation',
             #'WIND_AShareCompRestricted': 'WIND.AShareCompRestricted',
            'WIND_AShareCorporateFinance': 'WIND.AShareCorporateFinance',
            'WIND_AShareDescription': 'WIND.AShareDescription',
            'WIND_AShareDividend': 'WIND.AShareDividend',
            'WIND_AShareEnergyindexADJ': 'WIND.AShareEnergyindexADJ',
            'WIND_Ashareeoddindicator': 'WIND.AShareEODDerivativeIndicator',
            'WIND_AShareEODPrices': 'WIND.AShareEODPrices',
            'WIND_AShareEquityDivision': 'WIND.AShareEquityDivision',
            'WIND_AShareEquityPledgeInfo': 'WIND.AShareEquityPledgeInfo',
            'WIND_AShareEsopDescription': 'WIND.AShareEsopDescription',
            'WIND_AShareEsopTradingInfo': 'WIND.AShareEsopTradingInfo',
            'WIND_AShareEXRightDivRecord': 'WIND.AShareEXRightDividendRecord',
            'WIND_AShareFFCalendar': 'WIND.AShareFreeFloatCalendar',
            'WIND_AShareFloatHolder': 'WIND.AShareFloatHolder',
            'WIND_AShareFreeFloat': 'WIND.AShareFreeFloat',
            'WIND_AShareHolderNumber': 'WIND.AShareHolderNumber',
            'WIND_AShareIncDescription': 'WIND.AShareIncDescription',
            'WIND_AShareIncExecQtyPri': 'WIND.AShareIncExecQtyPri',
            'WIND_AShareIncExercisePct': 'WIND.AShareIncExercisePct',
            'WIND_AShareIncQuantityDetails': 'WIND.AShareIncQuantityDetails',
            'WIND_AShareIncQuantityPrice': 'WIND.AShareIncQuantityPrice',
            'WIND_AShareIndClassCITICS': 'WIND.AShareIndustriesClassCITICS',
            'WIND_AShareIndustriesCode': 'WIND.AShareIndustriesCode',
            'WIND_AShareInsideHolder': 'WIND.AShareInsideHolder',
            'WIND_AShareInsiderTrade': 'WIND.AShareInsiderTrade',
            'WIND_AShareinstHolderDerData': 'WIND.AShareinstHolderDerData',
            'WIND_AshareintensitytrendADJ': 'WIND.ASHAREINTENSITYTRENDADJ',
            'WIND_AShareIPO': 'WIND.AShareIPO',
            'WIND_AShareIssueCommAudit': 'WIND.AShareIssueCommAudit',
            'WIND_AShareL2Indicators': 'WIND.ASHAREL2INDICATORS',
            'WIND_AShareLeadUnderwriter': 'WIND.AShareLeadUnderwriter',
            'WIND_AShareMajorHolderPlanHold': 'WIND.AShareMajorHolderPlanHold',
            #'WIND_AShareManagement': 'WIND.AShareManagement',
            'WIND_AShareMarginSubject': 'WIND.AShareMarginSubject',
            'WIND_AShareMarginTrade': 'WIND.AShareMarginTrade',
            'WIND_AShareMarginTradeSum': 'WIND.AShareMarginTradeSum',
            #'WIND_AShareMgHoldReward': 'WIND.AShareManagementHoldReward',
            'WIND_AShareMoneyFlow': 'WIND.AShareMoneyFlow',
            'WIND_ASharePlacementDetails': 'WIND.ASharePlacementDetails',
            'WIND_ASharePlacementInfo': 'WIND.ASharePlacementInfo',
            'WIND_ASharePledgepro': 'WIND.ASharePledgeproportion',
            'WIND_AShareRightIssue': 'WIND.AShareRightIssue',
            'WIND_AShareSEO': 'WIND.AShareSEO',
            'WIND_AShareST': 'WIND.AShareST',
            'WIND_AShareStaff': 'WIND.AShareStaff',
            'WIND_AShareStaffStructure': 'WIND.AShareStaffStructure',
            'WIND_AshareStockRepo': 'WIND.AshareStockRepo',
            'WIND_AShareStrangeTrade': 'WIND.AShareStrangeTrade',
            'WIND_AShareStrangeTradedetail': 'WIND.AShareStrangeTradedetail',
            'WIND_AShareswingRevADJ': 'WIND.AShareswingReversetrendADJ',
            'WIND_AShareTechIndicators': 'WIND.AShareTechIndicators',
            'WIND_CMFOtherPortfolio': 'WIND.CMFOtherPortfolio',
            'WIND_CMFundAssetPortfolio': 'WIND.ChinaMutualFundAssetPortfolio',
            'WIND_CMFundBondPortfolio': 'WIND.ChinaMutualFundBondPortfolio',
            'WIND_CMFundIndPortfolio': 'WIND.ChinaMutualFundIndPortfolio',
            'WIND_CMFundStockPortfolio': 'WIND.ChinaMutualFundStockPortfolio',
            'WIND_CMMFPortfolioPTM': 'WIND.CMMFPortfolioPTM',
            'WIND_IECMemberList': 'WIND.IECMemberList',
            'WIND_IPOCompRFA': 'WIND.IPOCompRFA',
            'WIND_IPOInquiryDetails': 'WIND.IPOInquiryDetails',
            'WIND_SHSCChannelholdings': 'WIND.SHSCChannelholdings',
            'WIND_SHSCDailyStatistics': 'WIND.SHSCDailyStatistics',
            'WIND_SHSCShortselling': 'WIND.SHSCShortselling',
            'WIND_SHSCTop10ActiveStocks': 'WIND.SHSCTop10ActiveStocks',
            'WIND_AShareBalanceSheet': 'WIND.AShareBalanceSheet',
            'WIND_AShareCashFlow': 'WIND.AShareCashFlow',
            'WIND_AShareIncome': 'WIND.AShareIncome',
            'WIND_AShareProfitExpress': 'WIND.AShareProfitExpress',
            'WIND_AShareProfitNotice': 'WIND.AShareProfitNotice',
            'WIND_AShareFinancialIndicator': 'WIND.AShareFinancialIndicator',
            'WIND_AShareTTMHis': 'WIND.AShareTTMHis',
            'WIND_AShareAFIndicator': 'WIND.AShareAFIndicator',
            'WIND_AShareIssuingDatePredict': 'WIND.AShareIssuingDatePredict',
        }
        if self.table_name in table_alias:
            sql_select = 'select * from ' + table_alias[self.table_name]
        else:
            print('error: ' + self.table_name + ' not exists!')
            return
            #sql_select = 'select * from ' + self.table_name
        print(sql_select)

        # download data - save to csv 
        for date in self.cdate_list:
            if self.table_name in self.over_write_list:
                sql_use = sql_select + sql_where
            else:
                sql_use = sql_select + sql_where + str(date)
            print(sql_use)
            logger.info(sql_use)
            save_name = os.path.join(self.table_csv_path,str(date) + '.csv')
            # if os.path.exists(save_name):
            #     print('skip')
            #     continue
            # modify
            df = sql_parser(queryUserTableData(sql_use))
            if self.table_name in self.over_write_list:
                df['date'] = date
                save_name = os.path.join(self.table_csv_path,self.table_name + '.csv')
            df.set_index('OBJECT_ID', inplace = True)
            df.to_csv(save_name, sep=',', encoding='utf_8_sig')
            logger.info('retriever: saved in :  %s'%(save_name))

        logger.info('retriever: %s  done'%(self.table_name))
        
        return
    
        
    
    def dumper(self):
        logger.info('dump_h5: %s, %d, %d, %s, %s, %s'%(self.table_name,self.sdate,self.edate,self.ftype,self.dfreq,self.dsource))
            
        csv_list = [os.path.join(self.table_csv_path,i) for i in os.listdir(self.table_csv_path)]
        #modify 删除.h5结尾的项
        while True:
            found = False
            for item in csv_list:
                if item[-4:] != '.csv':
                    csv_list.remove(item)
                    found = True
            if not found:
                break

        csv_list.sort()
        if self.dfreq =='QUARTERLY':
            update_list = [i for i in csv_list if int(i[-12:-4])>=self.sdate-10000 and int(i[-12:-4])<=self.edate and int(i[-12:-4])>=20000101] # update for 1 year
        elif self.dfreq =='DAILY':
            if self.table_name in self.over_write_list:
                update_list = csv_list
            else:
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


def instantiate(table_name, sdate, edate, base_path, operation,table_dict):
    param_dict = get_table_param(table_name,table_dict)
    wind_db = WIND_DATABASE(table_name, sdate, edate, base_path, 
                            dfreq = param_dict['dfreq'],
                            operation = operation)    
    wind_db.retriever()
    if not table_name in ['WIND_AShareEquityPledgeInfo', 'WIND_AShareInsideHolder']:
       wind_db.dumper()
    else:
        print('Do not need to dump into h5')
    return 
 
if __name__ == '__main__':
    # sys.setdefaultencoding('utf-8')
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'

    sdate = 20180921
    edate = 20190115
    sdate,edate,cdate_list = check_update_date(sdate = sdate, edate = edate)
    #sdate,edate,cdate_list = check_update_date()

    qtr_list = ['WIND_AShareBalanceSheet','WIND_AShareCashFlow','WIND_AShareIncome','WIND_AShareProfitExpress',
                    'WIND_AShareProfitNotice','WIND_AShareFinancialIndicator','WIND_AShareTTMHis','WIND_AShareAFIndicator',
                    'WIND_AShareIssuingDatePredict']

    # modify 选择一个表测试
    #qtr_list = []

    daily_list =  ['WIND_AShareEODPrices','WIND_Ashareeoddindicator','WIND_SHSCDailyStatistics','WIND_SHSCShortselling',
                    'WIND_SHSCTop10ActiveStocks','WIND_SHSCChannelholdings', 'WIND_ASharePledgepro', 
                     'WIND_AShareFFCalendar',
                     'WIND_CMFundAssetPortfolio', 'WIND_CMFOtherPortfolio', 'WIND_CMFundIndPortfolio','WIND_CMFundStockPortfolio',
                     'WIND_CMFundBondPortfolio','WIND_AShareMarginTrade', 'WIND_AShareMarginSubject','WIND_AShareBlockTrade',
                     'WIND_AShareStrangeTradedetail', 'WIND_AShareStrangeTrade', 'WIND_AShareHolderNumber', 'WIND_AShareFloatHolder',
                      'WIND_AShareInsiderTrade', 'WIND_AShareMajorHolderPlanHold', 'WIND_AShareinstHolderDerData',
                      'WIND_AShareL2Indicators','WIND_CMMFPortfolioPTM', 'WIND_AShareMarginTradeSum', 'WIND_AShareIndClassCITICS',
                      'WIND_AShareDescription', 'WIND_AShareIndustriesCode', 'WIND_AShareMoneyFlow', 'WIND_AIndexEODPrices', 'WIND_AShareST']
    #modify 选择一个表测试
    daily_list = []
 

    new_daily_list = ['WIND_AShareCapitalization','WIND_AShareFreeFloat', 'WIND_AShareIPO', 'WIND_AShareAgency',
                'WIND_AShareCOCapitaloperation', 'WIND_AshareStockRepo', 'WIND_AShareCorporateFinance', 'WIND_AShareIssueCommAudit',
                'WIND_AShareEquityDivision', 'WIND_AShareMgHoldReward', 'WIND_AShareStaff', 'WIND_IPOCompRFA',
                'WIND_IECMemberList', 'WIND_AShareLeadUnderwriter','WIND_AShareDividend', 'WIND_AShareRightIssue',
                'WIND_AShareSEO', 'WIND_AShareEXRightDivRecord', 'WIND_AShareCompRestricted', 'WIND_ASharePlacementDetails',
                'WIND_ASharePlacementInfo', 'WIND_IPOInquiryDetails', 'WIND_AShareManagement', 'WIND_AShareIncDescription',
                'WIND_AShareIncQuantityPrice', 'WIND_AShareIncQuantityDetails','WIND_AShareIncExercisePct', 'WIND_AShareIncExecQtyPri',
                'WIND_AShareEsopDescription','WIND_AShareEsopTradingInfo', 'WIND_AShareStaffStructure','WIND_AShareEquityPledgeInfo', 'WIND_AShareInsideHolder']
    # modify 选择一个表测试
    new_daily_list = []

    tech_daily_list = [ 'WIND_AShareTechIndicators', 'WIND_AshareintensitytrendADJ', 'WIND_AShareEnergyindexADJ','WIND_AShareswingRevADJ']
    # modify 选择一个表测试
    tech_daily_list = []

    table_dict = {'QUARTERLY': qtr_list , 'DAILY': daily_list + new_daily_list + tech_daily_list}



    for table_type in table_dict:
        for table_name in table_dict[table_type]:
            print (table_name)
            # modify  base_path='Z:\\warehouse\\prod\\'
            try:
                instantiate(table_name, sdate, edate, base_path = '/app/data/wdb_h5/', operation = 'append',table_dict=table_dict)
            except:
                print('Failed:', table_name)       
            else:
                print('Success:', table_name)
    logger.info('===============upload finish======================')
