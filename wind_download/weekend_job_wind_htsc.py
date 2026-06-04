import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import os
from multiprocessing import Pool, Process, Manager
from multifactor.data.utils import *
import multifactor.utility.dt as tdt
import pickle
from xquant.factordata import FactorData
import time
from loguru import logger
from settings import BASE_DIR

s = FactorData()


def get_all_days(sdate, edate):
    # h5_path = '/data/group/800080/warehouse/prod/CALENDAR/nature_days.h5'
    h5_path = os.path.join(BASE_DIR, 'CALENDAR/nature_days.h5')
    df = IO.read_data([sdate, edate], alt=h5_path)
    df.reset_index(inplace=True)
    df['dt'] = df['dt'].apply(lambda x: int(str(x).replace('-', '')[:8]))
    date_list = list(set(df['dt']))
    date_list.sort()
    return date_list


class WIND_DATABASE:
    def __init__(self, table_name, sdate, edate,
                 base_path=BASE_DIR,
                 dtype='STOCK',
                 mkttype='CHINA',
                 ftype='FDD',
                 dfreq='QUARTERLY',
                 dsource='WIND',
                 operation='append'):

        self.table_name = table_name
        self.sdate = sdate
        self.edate = edate
        self.dtype = dtype
        self.mkttype = mkttype
        self.ftype = ftype
        self.dfreq = dfreq
        self.dsource = dsource
        self.base_path = base_path
        self.source_path = os.path.join(base_path, 'LOCAL_DATA/CSV/', dsource)
        self.operation = operation
        current_time = dt.datetime.strftime(dt.datetime.now(), '%Y%m%d')  # _%H%M%S')
        self.table_csv_path = os.path.join(self.source_path, self.table_name)
        name_mapping_dict = {}
        if self.table_name in name_mapping_dict:
            self.h5_name = name_mapping_dict[self.table_name]
        else:
            self.h5_name = self.table_name[5:]
        self.table_h5_path = os.path.join(self.base_path, 'DATABASE/WIND/', self.h5_name)
        self.table_h5_file = os.path.join(self.table_h5_path, self.h5_name + '.h5')
        for path in [self.table_csv_path, self.table_h5_path]:
            if not os.path.exists(path):
                logger.info('retriever: create folder:%s' % (path))
                os.makedirs(path)

        if self.dfreq == 'DAILY':
            self.cdate_list = get_all_days(sdate, edate)
        elif self.dfreq == 'QUARTERLY':
            qtr_list = get_qtr_list(self.sdate, self.edate, num_qtr=3)
            self.cdate_list = qtr_list
        else:
            raise Exception
        self.over_write_list = ['WIND_AShareIndustriesClassCITICS', 'WIND_AShareDescription',
                                'WIND_AShareIndustriesCode', 'WIND_AShareST',
                                'WIND_AShareCapitalization', 'WIND_AShareFreeFloat', 'WIND_AShareIPO',
                                'WIND_AShareAgency',
                                'WIND_AShareCOCapitaloperation', 'WIND_ASharePledgepro', 'WIND_AshareStockRepo',
                                'WIND_AShareCorporateFinance',
                                'WIND_AShareIssueCommAudit', 'WIND_AShareEquityDivision', 'WIND_AShareStaff',
                                'WIND_IPOCompRFA', 'WIND_IECMemberList', 'WIND_AShareLeadUnderwriter',
                                'WIND_AShareRightIssue', 'WIND_AShareSEO', 'WIND_IPOInquiryDetails',
                                'WIND_AShareManagement', 'WIND_AShareIncDescription', 'WIND_AShareIncQuantityPrice',
                                'WIND_AShareIncQuantityDetails',
                                'WIND_AShareIncExercisePct', 'WIND_AShareIncExecQtyPri', 'WIND_AShareEsopDescription',
                                'WIND_AShareEsopTradingInfo',
                                'WIND_AShareStaffStructure', 'WIND_AShareMajorHolderPlanHold', 'WIND_AShareTypeCode',
                                'WIND_htzqedbdzzbs',
                                'WIND_AShareMainandnoteitems', 'WIND_AIndexMembers', 'WIND_AShareConseption']

    def csv2h5(self, update_list, min_size=0):
        """
            operation = 'append': for existing one - if operation =='append' - will remove existing one 
            operation = 'create': remove completely 
            Removed by type_dropna
            sorted by type_sort - e.g. sorted by entry time
            for removing duplicate - just drop last row for subgroup 
        """
        dat_fig_dict = {'WIND_AShareProfitExpress': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareFinancialIndicator': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareProfitNotice': {'dt': 'S_PROFITNOTICE_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareTTMHis': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEODPrices': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEODDerivativeIndicator': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_SHSCDailyStatistics': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_EXCHMARKET'},
                        'WIND_SHSCTop10ActiveStocks': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_SHSCShortselling': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_SHSCChannelholdings': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareBalanceSheet': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCashFlow': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncome': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_CMMFPortfolioPTM': {'dt': 'REPORT_PERIOD', 'Ticker': 'F_INFO_WINDCODE'},
                        'WIND_CMFundAssetPortfolio': {'dt': 'F_PRT_ENDDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_CMFOtherPortfolio': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIllegality': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_CMFundIndPortfolio': {'dt': 'F_PRT_ENDDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_CMFundStockPortfolio': {'dt': 'ANN_DATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_CMFundBondPortfolio': {'dt': 'F_PRT_ENDDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMarginTrade': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMarginTradeSum': {'dt': 'TRADE_DT'},
                        'WIND_AIndexWindIndustriesEOD': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMarginSubject': {'dt': 'S_MARGIN_EFFECTDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMarginShortFeeRate': {'dt': 'EFFECTIVE_DATE'},
                        'WIND_AShareBlockTrade': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStrangeTradedetail': {'dt': 'START_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStrangeTrade': {'dt': 'S_STRANGE_BGDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareHolderNumber': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareInsideHolder': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareFloatHolder': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMjrHolderTrade': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareInsiderTrade': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMajorHolderPlanHold': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareinstHolderDerData': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMoneyFlow': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareL2Indicators': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_ASharePledgepro': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareFFCalendar': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIssuingDatePredict': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareANNFinancialIndicator': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIndustriesClassCITICS': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareDescription': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareConseption': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AIndexMembers': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMainandnoteitems': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIndustriesCode': {'dt': 'date'},
                        'WIND_AShareTypeCode': {'dt': 'date'},
                        'WIND_AIndexEODPrices': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareST': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCapitalization': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareFreeFloat': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIPO': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareAgency': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCOCapitaloperation': {'dt': 'date', 'Ticker': 'S_INFO_COMPCODE'},
                        'WIND_AshareStockRepo': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCorporateFinance': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIssueCommAudit': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEquityDivision': {'dt': 'date', 'Ticker': 'WINDCODE'},
                        'WIND_AShareManagementHoldReward': {'dt': 'ANN_DATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStaff': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_IPOCompRFA': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_IECMemberList': {'dt': 'date'},
                        'WIND_AShareLeadUnderwriter': {'dt': 'date'},
                        'WIND_AShareDividend': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareRightIssue': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareSEO': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEXRightDivRecord': {'dt': 'EX_DATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareCompRestricted': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareAnnInf': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_ASarePlanTrade': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_ASharePlacementDetails': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_ASharePlacementInfo': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_IPOInquiryDetails': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareManagement': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncDescription': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncQuantityPrice': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncQuantityDetails': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncExercisePct': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIncExecQtyPri': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEsopDescription': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEsopTradingInfo': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStaffStructure': {'dt': 'date', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareTechIndicators': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AshareintensitytrendADJ': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEnergyindexADJ': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareswingRevADJ': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_htzqedbdzzbs': {'dt': 'TDATE', 'Ticker': 'F3_4112'},
                        'WIND_FinNotesDetail': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareIBrokerIndicator': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareInsuranceIndicator': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareBankIndicator': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMonthlyReportsofBrokers': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AIndexIndustriesEODCITICS': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareAuditOpinion': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AIndexValuation': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AIndexFinancialderivative': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_SIndexPerformance': {'dt': 'TRADE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_BOIndexWeightsWIND': {'dt': 'CHANGE_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareStyleCoefficient': {'dt': 'S_CHANGE_DATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareTradingSuspension': {'dt': 'S_DQ_SUSPENDDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareSalesSegment': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_Top5ByLongTermBorrowing': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_Top5ByOperatingIncome': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_CBankFinNotes': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_COMPCODE'},
                        'WIND_AShareFinExpense': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AshareOthreceivables': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_COMPCODE'},
                        'WIND_Top5ByAccReceivable': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AshareInventorydetails': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_COMPCODE'},
                        'WIND_AshareFinaccounts': {'dt': 'REPORT_PERIOD', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareEquityPledgeInfo': {'dt': 'ANN_DT', 'Ticker': 'S_INFO_WINDCODE'},
                        'WIND_AShareMajorEvent': {'dt': 'S_EVENT_ANNCEDATE', 'Ticker': 'S_INFO_WINDCODE'},
                        }
        sparse_list = ['WIND_SHSCDailyStatistics', 'WIND_SHSCTop10ActiveStocks', 'WIND_SHSCShortselling',
                       'WIND_SHSCChannelholdings']

        logger.info('csv2h5: %s' % (self.table_name))
        dat_fig = dat_fig_dict[self.table_name]
        update_list.sort()

        if self.operation == 'create':
            logger.info('csv2h5: create -  %s' % (self.table_h5_file))
            os.remove(self.table_h5_file) if os.path.exists(self.table_h5_file) else None
        elif self.operation == 'append':
            logger.info('csv2h5: append -  %s' % (self.table_h5_file))

        if self.table_name in self.over_write_list:
            logger.info('csv2h5: create -  %s' % (self.table_h5_file))
            os.remove(self.table_h5_file) if os.path.exists(self.table_h5_file) else None

        with pd.HDFStore(self.table_h5_file) as h5_store:
            logger.info('csv2h5: check date list')
            if self.table_name in list(h5_store.root._v_groups.keys()):
                dt_lst = list(set(h5_store.select_column(self.table_name, 'dt')))
            else:
                dt_lst = []
            for fname in update_list:
                if not '.csv' in fname:
                    continue
                logger.info(fname)
                dat1 = pd.read_csv(fname, encoding='utf_8_sig')

                if len(dat1) <= min_size:
                    if self.table_name in sparse_list:
                        logger.warning('csv2h5: sparse table %s - data too little ' % (self.table_name))
                        pass
                    else:
                        logger.error('csv2h5: source data %s too little!' % (self.table_name))
                        pass
                else:
                    if self.table_name == 'WIND_AShareMarginShortFeeRate':
                        dat1['PUBLISHER_ID'] = dat1['PUBLISHER_ID'].astype(str)

                    if self.table_name == 'WIND_AShareAnnInf':
                        dat1['ANN_DT'] = dat1['ANN_DT'].apply(lambda x: int(str(x).replace('-', '')[:8]))
                    dat = data_reformat(dat1, dat_fig)
                    if self.operation == 'append':
                        curr_date = list(set(dat.index.get_level_values('dt')))[0]
                        print(curr_date)
                        if curr_date in dt_lst:
                            logger.info('csv2h5: exist: %s' % (curr_date))
                            # print('pass')
                            # continue
                            dummy_id = h5_store.remove(self.table_name, 'dt=curr_date')
                            logger.info('csv2h5: append: %s' % (curr_date))
                    if self.table_name == 'WIND_AShareProfitNotice':
                        dat['OBJECT_ID'] = dat['OBJECT_ID'].astype(str)
                        dat['S_PROFITNOTICE_REASON'] = dat['S_PROFITNOTICE_REASON'].astype(str)
                        dat.drop(['S_PROFITNOTICE_ABSTRACT', 'S_PROFITNOTICE_REASON'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'OBJECT_ID': 100})

                    elif self.table_name == 'WIND_SHSCDailyStatistics':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 10})
                    elif self.table_name == 'WIND_SHSCChannelholdings':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_INFO_EXCHMARKETNAME': 10})
                    elif self.table_name == 'WIND_SHSCTop10ActiveStocks':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'MARKET': 10, 'S_INFO_EXCHMARKETNAME': 10})
                    elif self.table_name == 'WIND_CMFOtherPortfolio':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype('object')
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 15, 'S_INFO_HOLDWINDCODE': 15})
                    elif self.table_name == 'WIND_AShareIllegality':
                        # print(dat.dtypes)
                        dat.drop(['BEHAVIOR', 'METHOD', 'REF_RULE'], axis=1, inplace=True)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        dat['SUBJECT'] = dat['SUBJECT'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'DISPOSAL_TYPE': 200, 'S_INFO_COMPCODE': 40, 'ILLEG_TYPE': 200,
                                                      'SUBJECT': 200, 'PROCESSOR': 400})
                    elif self.table_name == 'WIND_CMFundStockPortfolio':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype('object')
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_CMFundBondPortfolio':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype('object')
                        dat['S_INFO_BONDWINDCODE'] = dat['S_INFO_BONDWINDCODE'].astype('object')
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_INFO_BONDWINDCODE': 15})
                    elif self.table_name == 'WIND_AShareMarginSubject':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_AShareMarginShortFeeRate':
                        h5_store.append(self.table_name, dat, data_columns=True)
                    elif self.table_name == 'WIND_AShareBlockTrade':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_BLOCK_SELLERNAME': 150, 'S_BLOCK_BUYERNAME': 150})
                    elif self.table_name == 'WIND_AShareStrangeTrade':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_STRANGE_TRADERNAME': 150})
                    elif self.table_name == 'WIND_AShareInsideHolder':
                        dat.drop(['S_HOLDER_MEMO'], axis=1, inplace=True)
                        dat['S_HOLDER_SEQUENCE'] = dat['S_HOLDER_SEQUENCE'].astype(str)
                        dat['S_HOLDER_SHARECATEGORYNAME'] = dat['S_HOLDER_SHARECATEGORYNAME'].astype(str)
                        dat['S_HOLDER_SHARECATEGORY'] = dat['S_HOLDER_SHARECATEGORY'].astype(str)
                        # print(dat.dtypes)

                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'S_HOLDER_NAME': 200,
                                                                                               'S_HOLDER_ANAME': 200,
                                                                                               'S_HOLDER_SEQUENCE': 200,
                                                                                               'S_HOLDER_SHARECATEGORYNAME': 200,
                                                                                               'S_HOLDER_SHARECATEGORY': 200})
                    elif self.table_name == 'WIND_AShareFloatHolder':
                        dat['S_HOLDER_WINDNAME'] = dat['S_HOLDER_WINDNAME'].astype('object')
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_HOLDER_NAME': 175, 'S_HOLDER_WINDNAME': 175})
                    elif self.table_name == 'WIND_AShareMjrHolderTrade':
                        dat.drop(['TRADE_DETAIL', 'HOLDER_NAME'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True)
                    elif self.table_name == 'WIND_AShareInsiderTrade':
                        dat.drop(['IS_SHORT_TERM_TRADE'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'RELATED_MANAGER_POST': 100, 'RELATED_MANAGER_NAME': 100,
                                                      'REPORTED_TRADER_NAME': 150,
                                                      'TRADER_MANAGER_RELATION': 150})
                    elif self.table_name == 'WIND_AShareinstHolderDerData':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'S_HOLDER_NAME': 500})

                    elif self.table_name == 'WIND_AShareIssuingDatePredict':
                        dat.drop(['S_STM_CORRECT_ISSUINGDATE'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True)
                    elif self.table_name == 'WIND_AShareANNFinancialIndicator':
                        dat.drop(['MEMO', 'S_INFO_DIV'], axis=1, inplace=True)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'S_INFO_COMPCODE': 15})
                    elif self.table_name == 'WIND_AShareEXRightDivRecord':
                        dat['EX_TYPE'] = dat['EX_TYPE'].astype('object')
                    elif self.table_name == 'WIND_ASharePlacementDetails':
                        dat['S_HOLDER_NAME'] = dat['S_HOLDER_NAME'].astype('object')
                        dat['TYPEOFINVESTOR'] = dat['TYPEOFINVESTOR'].astype('object')
                        dat['S_HOLDER_TYPE'] = dat['S_HOLDER_TYPE'].astype('object')
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_HOLDER_NAME': 200, 'TYPEOFINVESTOR': 50, 'S_HOLDER_TYPE': 75})
                    elif self.table_name == 'WIND_AIndexEODPrices':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 15, 'SEC_ID': 10})
                    elif self.table_name == 'WIND_AShareProfitExpress':
                        dat.drop(['BRIEF_PERFORMANCE', 'MEMO'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True)

                    elif self.table_name == 'WIND_AShareBalanceSheet':
                        dat.drop(['LEASE_LIAB', 'RECEIVABLES_FINANCING', 'RIGHT_USE_ASSETS'], axis=1, inplace=True)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True)

                    elif self.table_name == 'WIND_AShareCashFlow':
                        dat.drop(['CREDIT_IMPAIRMENT_LOSS', 'OTHER_IMPAIR_LOSS_ASSETS', 'RIGHT_USE_ASSETS_DEP'], axis=1,
                                 inplace=True)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'S_INFO_COMPCODE': 20})

                    elif self.table_name == 'WIND_AShareIncome':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        dat.drop(['MEMO'], axis=1, inplace=True)
                        # print(dat.dtypes)
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'S_INFO_COMPCODE': 20})

                    elif self.table_name == 'WIND_AShareTTMHis':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True)

                    elif self.table_name == 'WIND_AShareFinancialIndicator':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True)

                    elif self.table_name == 'WIND_AshareintensitytrendADJ':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_AShareEnergyindexADJ':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_AShareswingRevADJ':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 15})
                    elif self.table_name == 'WIND_htzqedbdzzbs':
                        dat.drop(['date'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True)
                    elif self.table_name == 'WIND_AShareManagementHoldReward':
                        dat['S_INFO_MANAGER_NAME'] = dat['S_INFO_MANAGER_NAME'].astype(str)
                        dat['S_INFO_MANAGER_POST'] = dat['S_INFO_MANAGER_POST'].astype(str)
                        dat['MANID'] = dat['MANID'].astype(str)
                        dat['CRNY_CODE'] = dat['CRNY_CODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_INFO_MANAGER_NAME': 100, 'S_INFO_MANAGER_POST': 100,
                                                      'MANID': 35})

                    elif self.table_name == 'WIND_AShareIBrokerIndicator':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'STATEMENT_TYPE': 10})

                    elif self.table_name == 'WIND_AShareInsuranceIndicator':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True)
                    elif self.table_name == 'WIND_AShareDividend':
                        dat['S_DIV_OBJECT'] = dat['S_DIV_OBJECT'].astype(str)
                        dat.drop(['S_DIV_CHANGE', 'MEMO', 'IS_TRANSFER'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'S_DIV_OBJECT': 100})
                    elif self.table_name == 'WIND_AShareMonthlyReportsofBrokers':
                        dat.reset_index('Ticker', inplace=True)

                        def help(df):
                            comp = df['S_INFO_COMPCODE']
                            # with open('/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/comp_dict.pickle', 'rb') as file:
                            with open(os.path.join(BASE_DIR, 'LOCAL_DATA/CSV/WIND/comp_dict.pickle'),
                                      'rb') as file:
                                comp_dict = pickle.load(file)
                            if comp in comp_dict:
                                return comp_dict[comp]
                            else:
                                return np.nan

                        dat['Ticker'] = dat.apply(lambda x: help(x), axis=1)
                        dat.dropna(subset=['Ticker'], inplace=True)
                        dat.reset_index('dt', inplace=True)
                        dat.set_index(['dt', 'Ticker'], inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_INFO_COMPNAME': 100})
                    elif self.table_name == 'WIND_AIndexIndustriesEODCITICS':
                        dat['CRNCY_CODE'] = dat['CRNCY_CODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True)

                    elif self.table_name == 'WIND_AShareAuditOpinion':
                        dat.drop(['S_AUDIT_RESULT_MEMO', 'S_AUDIT_FEE_MEMO', 'S_IN_CONTROL_AUDIT'], axis=1,
                                 inplace=True)
                        dat['S_STMNOTE_AUDIT_CPA'] = dat['S_STMNOTE_AUDIT_CPA'].astype(str)
                        dat['S_IN_CONTROL_ACCOUNTING_FIRM'] = dat['S_IN_CONTROL_ACCOUNTING_FIRM'].astype(str)
                        dat['S_IN_CONTROL_ACCOUNTANT'] = dat['S_IN_CONTROL_ACCOUNTANT'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_STMNOTE_AUDIT_AGENCY': 100,
                                                      'S_STMNOTE_AUDIT_CPA': 100, 'S_IN_CONTROL_ACCOUNTING_FIRM': 100,
                                                      'S_IN_CONTROL_ACCOUNTANT': 100})

                    elif self.table_name == 'WIND_AIndexValuation':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 40})
                    elif self.table_name == 'WIND_AIndexFinancialderivative':
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 40})
                    elif self.table_name in ['WIND_SIndexPerformance', 'WIND_AShareStyleCoefficient']:
                        h5_store.append(self.table_name, dat, data_columns=True, min_itemsize={'Ticker': 40})
                    elif self.table_name == 'WIND_BOIndexWeightsWIND':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_INFO_INDEX_WEIGHTSRULE': 10})
                    elif self.table_name == 'WIND_AShareTradingSuspension':
                        dat.drop(['S_DQ_CHANGEREASON'], axis=1, inplace=True)
                        dat['S_DQ_TIME'] = dat['S_DQ_TIME'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_DQ_TIME': 200})

                    elif self.table_name == 'WIND_AShareSEO':
                        dat.drop(['S_FELLOW_OFFERINGOBJECT_DES', 'S_FELLOW_OBJECTIVE', 'PRICE_CONDITION',
                                  'S_FELLOW_OFFERINGOBJECT'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True)
                    elif self.table_name == 'WIND_AShareSalesSegment':
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_SEGMENT_ITEM': 200})
                    elif self.table_name == 'WIND_Top5ByLongTermBorrowing':
                        dat['RATE'] = dat['RATE'].astype(str)
                        dat.drop(['S_INFO_COMPNAME', 'S_INFO_COMPCODE2'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'RATE': 150, 'CRNCY_CODE': 10})
                    elif self.table_name == 'WIND_Top5ByOperatingIncome':
                        dat.drop(['S_INFO_COMPNAME', 'S_INFO_COMPCODE2'], axis=1, inplace=True)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)

                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_INFO_COMPCODE': 50})
                    elif self.table_name == 'WIND_CBankFinNotes':
                        dat.drop(['ANN_ITEM', 'ITEM_NAME'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'ITEM_DATA': 100, 'STATEMENT_TYPE': 200})
                    elif self.table_name == 'WIND_AshareOthreceivables':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 150, 'DEBTOR_NAME': 150, 'STATEMENT_TYPE': 200})
                    elif self.table_name == 'WIND_Top5ByAccReceivable':
                        dat.drop(['REASON'], axis=1, inplace=True)
                        dat['S_INFO_COMPNAME'] = dat['S_INFO_COMPNAME'].astype(str)
                        dat['S_INFO_COMPCODE'] = dat['S_INFO_COMPCODE'].astype(str)
                        dat['PERIOD'] = dat['PERIOD'].astype(str)

                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'S_INFO_COMPCODE': 70, 'S_INFO_COMPNAME': 150,
                                                      'CRNCY_CODE': 10, 'PERIOD': 100})
                    elif self.table_name == 'WIND_AshareInventorydetails':
                        dat.drop(['INV_OBJECT'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'CRNCY_CODE': 10, 'SUBJECT_NAME': 50})
                    elif self.table_name == 'WIND_AshareFinaccounts':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'Ticker': 40, 'STATEMENT_TYPE': 100, 'SUBJECT_CHINESE_NAME': 200,
                                                      'CLASSIFICATION_NUMBER': 20, 'S_INFO_DATATYPE': 80,
                                                      'ANN_ITEM': 200,
                                                      'ITEM_NAME': 200})
                    elif self.table_name == 'WIND_AShareEquityPledgeInfo':
                        dat['S_HOLDER_ID'] = dat['S_HOLDER_ID'].astype(str)
                        dat['S_PLEDGOR_ID'] = dat['S_PLEDGOR_ID'].astype(str)
                        dat.drop(['S_HOLDER_NAME', 'S_PLEDGOR', 'S_REMARK'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_HOLDER_ID': 15, 'S_PLEDGOR_ID': 15})
                    elif self.table_name == 'WIND_AShareCompRestricted':
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'S_HOLDER_NAME': 200, 'S_SHARE_LSTTYPENAME': 200})
                    elif self.table_name == 'WIND_AShareAnnInf':
                        dat['N_INFO_FCODE'] = dat['N_INFO_FCODE'].astype(str)
                        dat.drop(['N_INFO_ANNLINK', 'N_INFO_FTXT'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'N_INFO_TITLE': 1500, 'N_INFO_FCODE': 500, 'N_INFO_STOCKID': 20,
                                                      'N_INFO_COMPANYID': 20})

                    elif self.table_name == 'WIND_ASarePlanTrade':
                        dat['TRANSACT_STOCK_SOURCE'] = dat['TRANSACT_STOCK_SOURCE'].astype(str)
                        dat['TRANSACT_SOURCE_FUNDS'] = dat['TRANSACT_SOURCE_FUNDS'].astype(str)
                        dat['TRANSACT_PERIOD_DESCRIPTION'] = dat['TRANSACT_PERIOD_DESCRIPTION'].astype(str)
                        dat['TRANSACTION_MODE'] = dat['TRANSACTION_MODE'].astype(str)
                        dat['VARIABLE_PRICE_MEMO'] = dat['VARIABLE_PRICE_MEMO'].astype(str)

                        dat.drop(['SPECIAL_CHANGES_MEMO', 'PROGRAM_ADJUSTMENT_MEMO', 'TRANSACT_OBJECTIVE'], axis=1,
                                 inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True,
                                        min_itemsize={'HOLDER_NAME': 500, 'TRANSACT_STOCK_SOURCE': 200,
                                                      'TRANSACT_SOURCE_FUNDS': 200,
                                                      'HOLDER_STATUS': 100, 'TRANSACT_PERIOD_DESCRIPTION': 200,
                                                      'TRANSACTION_MODE': 200,
                                                      'VARIABLE_PRICE_MEMO': 200})

                    elif self.table_name == 'WIND_AShareMajorEvent':
                        dat.drop(['S_EVENT_CONTENT'], axis=1, inplace=True)
                        h5_store.append(self.table_name, dat, data_columns=True)

                    else:
                        h5_store.append(self.table_name, dat, data_columns=True)

                    logger.info('csv2h5: %s done' % (fname))

        logger.info('csv2h5 all done: %s' % (self.table_name))
        return

        # different tables - different paremeters - get dataframe

    def get_df(self, date):

        print(date)

        if self.table_name in ['WIND_AShareFinancialIndicator', 'WIND_AShareProfitExpress', 'WIND_AShareTTMHis',
                               'WIND_AShareBalanceSheet', 'WIND_AShareCashFlow', 'WIND_AShareIncome',
                               'WIND_CMMFPortfolioPTM',
                               'WIND_AShareinstHolderDerData', 'WIND_AShareIssuingDatePredict',
                               'WIND_AShareANNFinancialIndicator',
                               'WIND_FinNotesDetail', 'WIND_AShareIBrokerIndicator', 'WIND_AShareInsuranceIndicator',
                               'WIND_AShareBankIndicator',
                               'WIND_AShareAuditOpinion', 'WIND_AIndexFinancialderivative', 'WIND_AShareSalesSegment',
                               'WIND_Top5ByLongTermBorrowing', 'WIND_Top5ByOperatingIncome', 'WIND_CBankFinNotes',
                               'WIND_AShareFinExpense',
                               'WIND_AshareOthreceivables', 'WIND_Top5ByAccReceivable', 'WIND_AshareInventorydetails',
                               'WIND_AshareFinaccounts',
                               'WIND_AShareDividend']:
            df = s.get_factor_value(self.table_name, report_period=[str(date)])

        elif self.table_name in ['WIND_AShareMonthlyReportsofBrokers']:
            df = s.get_factor_value('WIND_AShareMonthlyReportsofBrokers', report_period=[str(date)])

        elif self.table_name in ['WIND_AShareProfitNotice']:
            df = s.get_factor_value(self.table_name, S_ProfitNotice_Period=[str(date)])

        elif self.table_name in ['WIND_AShareEODPrices', 'WIND_AShareEODDerivativeIndicator',
                                 'WIND_SHSCDailyStatistics',
                                 'WIND_SHSCShortselling', 'WIND_SHSCTop10ActiveStocks', 'WIND_SHSCChannelholdings',
                                 'WIND_AShareMarginTrade', 'WIND_AShareMarginTradeSum', 'WIND_AShareBlockTrade',
                                 'WIND_AShareInsiderTrade', 'WIND_AShareMoneyFlow', 'WIND_AShareL2Indicators',
                                 'WIND_AIndexEODPrices', 'WIND_ASharePlacementDetails', 'WIND_ASharePlacementInfo',
                                 'WIND_AShareTechIndicators',
                                 'WIND_AshareintensitytrendADJ', 'WIND_AShareEnergyindexADJ', 'WIND_AShareswingRevADJ',
                                 'WIND_AIndexIndustriesEODCITICS', 'WIND_AIndexValuation', 'WIND_SIndexPerformance',
                                 'WIND_AIndexWindIndustriesEOD']:
            df = s.get_factor_value(self.table_name, trade_dt=[str(date)])
        elif self.table_name in ['WIND_CMFundAssetPortfolio', 'WIND_CMFundIndPortfolio', 'WIND_CMFundBondPortfolio']:
            df = s.get_factor_value(self.table_name, F_PRT_ENDDATE=[str(date)])
        elif self.table_name in ['WIND_CMFOtherPortfolio', 'WIND_AShareHolderNumber', 'WIND_AShareIllegality',
                                 'WIND_AShareInsideHolder', 'WIND_AShareMjrHolderTrade', 'WIND_AShareFloatHolder',
                                 'WIND_AShareFFCalendar', 'WIND_AShareEquityPledgeInfo', 'WIND_AShareCompRestricted',
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
            logger.error('retriever: table not defined: %s' % (self.table_name))
            raise Exception

        return df

    def retriever(self):

        logger.info('下载数据: source_table={}, data={}-{}, csv_path={}'.format(self.table_name, self.sdate, self.edate,
                                                                            self.table_csv_path))

        # download data - save to csv
        if self.table_name == 'WIND_AShareMonthlyReportsofBrokers':
            _, _, tmp_date_list = check_update_date(sdate=20040101, edate=self.cdate_list[-1])
            new_cdate_list = []
            month_dict = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
            for date in self.cdate_list:
                year = int(int(date) / 10000)
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
                sql_use = str(date)
                # logger.info(sql_use)
                save_name = os.path.join(self.table_csv_path, str(date) + '.csv')
                try:
                    df = s.get_factor_value('WIND_AShareMonthlyReportsofBrokers', report_period=[str(date)])

                    def help(df, tmp_date_list):
                        date = df['ANN_DT']
                        date = int(date)
                        while date not in tmp_date_list and date < tmp_date_list[-1]:
                            date += 1
                        return str(date)

                    df['ANN_DT_modified'] = df.apply(lambda x: help(x, tmp_date_list), axis=1)
                    df.set_index('OBJECT_ID', inplace=True)
                    df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                    logger.info('retriever: saved in :  %s' % (save_name))
                except Exception as err:
                    if len(df) == 0:
                        df.to_csv(save_name, sep=',', encoding='utf_8_sig')

                    logger.warning('%s got exception as follows: ' % (self.table_name))
                    print(err)

        else:
            if self.table_name in self.over_write_list:
                try:
                    df = s.get_factor_value(self.table_name)
                    df['date'] = self.cdate_list[-1]
                    save_name = os.path.join(self.table_csv_path, self.table_name + '.csv')
                    df.set_index('OBJECT_ID', inplace=True)
                    df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                    logger.info('retriever: saved in :  %s' % (save_name))
                except Exception as err:
                    logger.warning('%s got exception as follows: ' % (self.table_name))
                    print(err)
                    df1 = s.get_factor_value(self.table_name, OPDATE=['>=20140601'])
                    df = df1.append(s.get_factor_value(self.table_name, OPDATE=['<20140601']))
                    df['date'] = self.cdate_list[-1]
                    save_name = os.path.join(self.table_csv_path, self.table_name + '.csv')
                    df.set_index('OBJECT_ID', inplace=True)
                    df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                    logger.info('retriever: saved in :  %s' % (save_name))
            else:
                for date in self.cdate_list:
                    try:
                        df = self.get_df(date)
                        save_name = os.path.join(self.table_csv_path, str(date) + '.csv')
                        df.set_index('OBJECT_ID', inplace=True)
                        df.to_csv(save_name, sep=',', encoding='utf_8_sig')
                        logger.info('retriever: saved in :  %s' % (save_name))
                    except Exception as err:
                        logger.warning('%s got exception as follows: ' % (self.table_name))
                        print(err)

        logger.info('retriever: %s  done' % (self.table_name))
        return

    def dumper(self):
        logger.info('dump_h5: %s, %d, %d, %s, %s, %s' % (
            self.table_name, self.sdate, self.edate, self.ftype, self.dfreq, self.dsource))

        csv_list = [os.path.join(self.table_csv_path, i) for i in os.listdir(self.table_csv_path)]
        # print('@@@@@@@@@@@@@@@')
        # print(csv_list)
        csv_list.sort()

        if self.dfreq == 'QUARTERLY':
            update_list = [i for i in csv_list if
                           int(i[-12:-4]) >= self.sdate - 10000 and int(i[-12:-4]) <= self.edate and int(
                               i[-12:-4]) >= 20000101]  # update for 1 year
        elif self.dfreq == 'DAILY':
            if self.table_name in self.over_write_list:
                update_list = csv_list
            elif self.table_name == 'WIND_AShareMonthlyReportsofBrokers':
                new_cdate_list = []
                update_list = []
                month_dict = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
                for date in self.cdate_list:
                    year = int(int(date) / 10000)
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
                        update_list.append(os.path.join(self.table_csv_path, str(month_date) + '.csv'))
                        print(update_list)
            else:
                # print(csv_list)
                update_list = [i for i in csv_list if
                               int(i[-12:-4]) >= self.sdate and int(i[-12:-4]) <= self.edate and int(
                                   i[-12:-4]) >= 20000101]
        self.csv2h5(update_list)

        return


def get_table_param(table_name, table_dict):
    param_dict = {}
    if table_name in table_dict['QUARTERLY']:
        param_dict['dfreq'] = 'QUARTERLY'
    elif table_name in table_dict['DAILY']:
        param_dict['dfreq'] = 'DAILY'
    else:
        print('table not defined: %s' % table_name)
        raise Exception
    return param_dict


def instantiate(table_name, sdate, edate, base_path, operation, table_dict, update_h5_flag=False):
    # get dfreq
    param_dict = get_table_param(table_name, table_dict)
    wind_db = WIND_DATABASE(table_name, sdate, edate, base_path,
                            dfreq=param_dict['dfreq'],
                            operation=operation)
    wind_db.retriever()
    # if update_h5_flag:
    wind_db.dumper()
    flag_root = BASE_DIR + '/LOCAL_DATA/FLAG/' + str(edate) + '/RDF/'
    table_name = table_name[5:]
    if not os.path.exists(flag_root):
        os.makedirs(flag_root)
    with open(flag_root + table_name + '.success', 'w') as file:
        pass
    return


def first_job(sdate, edate):
    qtr_list = ['WIND_AShareBalanceSheet', 'WIND_AShareCashFlow', 'WIND_AShareIncome', 'WIND_AShareProfitExpress',
                'WIND_AShareProfitNotice', 'WIND_AShareFinancialIndicator', 'WIND_AShareTTMHis',
                'WIND_AShareANNFinancialIndicator',
                'WIND_AShareIssuingDatePredict', 'WIND_AShareDividend', 'WIND_AIndexFinancialderivative']

    qtr_list2 = ['WIND_AShareSalesSegment', 'WIND_AShareFinExpense', 'WIND_AShareAuditOpinion',
                 'WIND_AShareIBrokerIndicator', 'WIND_AShareBankIndicator', 'WIND_AShareInsuranceIndicator']

    daily_list = ['WIND_AShareDescription', 'WIND_AShareIndustriesClassCITICS', 'WIND_AShareST',
                  'WIND_AShareManagement',
                  'WIND_AShareMonthlyReportsofBrokers', 'WIND_AShareManagementHoldReward', 'WIND_AIndexMembers',
                  'WIND_AShareConseption',
                  'WIND_AShareRightIssue']

    daily_list2 = ['WIND_AShareStaff', 'WIND_AShareIPO', 'WIND_AShareSEO', 'WIND_AShareMjrHolderTrade']
    table_dict = {'QUARTERLY': qtr_list + qtr_list2, 'DAILY': daily_list + daily_list2}
    for table_type in table_dict:
        for table_name in table_dict[table_type]:
            print(table_name)
            instantiate(table_name, sdate, edate, base_path=BASE_DIR, operation='append', table_dict=table_dict)

    logger.info('===============1st job upload finish======================')
