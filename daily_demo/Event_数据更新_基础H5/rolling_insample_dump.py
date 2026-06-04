from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import datetime as dt

import pandas as pd
import numpy as np
import time
import os
from concurrent.futures import ProcessPoolExecutor as Pool
from concurrent.futures import as_completed

def RDF_daily(sdate,edate,operation='append'):
    over_write_list = ['WIND_AShareIndustriesClassCITICS', 'WIND_AShareDescription', 'WIND_AShareIndustriesCode','WIND_AShareST',
                        'WIND_AShareCapitalization', 'WIND_AShareFreeFloat', 'WIND_AShareIPO', 'WIND_AShareAgency',
                         'WIND_AShareCOCapitaloperation', 'WIND_ASharePledgepro', 'WIND_AshareStockRepo', 'WIND_AShareCorporateFinance',
                         'WIND_AShareIssueCommAudit', 'WIND_AShareEquityDivision', 'WIND_AShareStaff',
                         'WIND_IPOCompRFA', 'WIND_IECMemberList', 'WIND_AShareLeadUnderwriter',
                         'WIND_AShareRightIssue', 'WIND_AShareSEO', 'WIND_IPOInquiryDetails',
                         'WIND_AShareManagement', 'WIND_AShareIncDescription', 'WIND_AShareIncQuantityPrice', 'WIND_AShareIncQuantityDetails',
                         'WIND_AShareIncExercisePct', 'WIND_AShareIncExecQtyPri', 'WIND_AShareEsopDescription', 'WIND_AShareEsopTradingInfo',
                         'WIND_AShareStaffStructure', 'WIND_AShareMajorHolderPlanHold','WIND_AShareTypeCode','WIND_htzqedbdzzbs',
                         'WIND_AShareMainandnoteitems','WIND_AIndexMembers','WIND_AShareConseption']
    
    table_list = ['WIND_AShareBalanceSheet','WIND_AShareCashFlow','WIND_AShareIncome','WIND_AShareProfitExpress',
                'WIND_AShareProfitNotice','WIND_AShareFinancialIndicator','WIND_AShareTTMHis', 'WIND_AShareANNFinancialIndicator', 
                'WIND_AShareIssuingDatePredict','WIND_AShareDividend','WIND_AIndexFinancialderivative',
                'WIND_AShareDescription','WIND_AShareIndustriesClassCITICS','WIND_AShareST', 'WIND_AShareManagement',
                'WIND_AShareMonthlyReportsofBrokers','WIND_AShareEODDerivativeIndicator',
                'WIND_AShareEODPrices','WIND_AIndexEODPrices','WIND_AIndexValuation',
                'WIND_AShareManagementHoldReward','WIND_AShareMoneyFlow',
                'WIND_AShareL2Indicators','WIND_AIndexMembers','WIND_AShareConseption',
                'WIND_AShareTechIndicators', 'WIND_AshareintensitytrendADJ', 'WIND_AShareEnergyindexADJ']
                

    root1 = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    root2 = '/data/group/800080/warehouse/insample/DATABASE/WIND/'
    for dataset_name in table_list:
        table_name = dataset_name[5:]
        if not os.path.exists(root2 + table_name):
            os.makedirs(root2 + table_name)
        table_h5_file1 = root1 + table_name + '/' + table_name + '.h5'
        table_h5_file2 = root2 + table_name + '/' + table_name + '.h5'
        if dataset_name in over_write_list:
            os.system('cp ' + table_h5_file1 + ' ' + table_h5_file2)
            continue
        with pd.HDFStore(table_h5_file2) as h5_store:

            dat = IO.read_data([sdate,edate],alt=table_h5_file1)
            if dataset_name in list(h5_store.root._v_groups.keys()):
                dt_lst = list(set(h5_store.select_column(dataset_name, 'dt')))
            else:
                dt_lst = []

            if operation == 'append':      
                cur_date_list = list(set(dat.index.get_level_values('dt')))
                for curr_date in cur_date_list:
                    print (curr_date)
                    if curr_date in dt_lst:
                        print('csv2h5: exist: %s'%(curr_date))
                        dummy_id = h5_store.remove(dataset_name,'dt=curr_date')
                        print('csv2h5: removed: %s'%(curr_date))

            h5_store.append(dataset_name,dat,data_columns=True)


def h5_trans(sdate,edate,append_flag=True):
    # md_h5='MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5'
    # index_md_h5='MD/CHINA_INDEX/DAILY/WIND/MD_CHINA_INDEX_DAILY_WIND.h5'
    FDD_qtr_h5 = 'FDD/CHINA_STOCK/QUARTERLY/WIND/FDD_CHINA_STOCK_QUARTERLY_WIND.h5'
    FDD_daily_h5 = 'FDD/CHINA_STOCK/DAILY/WIND/FDD_CHINA_STOCK_DAILY_WIND.h5'
    RISK_daily_h5 = 'RISK/CHINA_STOCK/DAILY/STYLEFACTOR/RISK_CHINA_STOCK_DAILY_STYLEFACTOR.h5'
    UNIV_h5 = 'UNIV/CHINA_STOCK/DAILY/OPTM/UNIV_CHINA_STOCK_DAILY_OPTM.h5'

    root = '/data/group/800080/warehouse/prod/'
    root_insample = '/data/group/800080/warehouse/insample/'
    
    h5_list = [FDD_qtr_h5, FDD_daily_h5, RISK_daily_h5]

    for path in h5_list:
        file1 = os.path.join(root,path)
        file_insample = os.path.join(root_insample, path)
        df = IO.read_data([sdate,edate], alt = file1)
        for col in list(df.columns):
            print(col)
            df1 = df[[col]]
            IO.pd_hdf5_writer(df1, file_insample, dataset=col,append=append_flag)
    
    univ_file = os.path.join(root,UNIV_h5)
    univ_file_insample = os.path.join(root_insample,UNIV_h5)
    df = IO.read_data([sdate,edate],alt=univ_file)
    IO.pd_hdf5_writer(df,univ_file_insample,dataset='stock_universe',append=append_flag)

def b_tables(sdate,edate,append=True):
    b_list = ['con_forecast_stk', 'con_forecast_schedule','stock_order3','stock_report_adjustment',
                  'stock_report_number','stock_order2','stock_report_adjustment2','stock_concern_level',
                  'con_stock_deviation3','con_stock_deviation2','con_stock_deviation',
                  'stock_diversity','stock_emotion','stock_report_extremum',
                  'der_report_subtable', 'cmb_report_score_adjust', 'i_organ_score', 'report_author', 
                  'cmb_report_adjust', 'gg_org_list', 'i_report_type', 'author_core_type', 'author_core',
                  'cmb_report_subtable', 'author_pj', 'author_pjhb', 't_great_author',
                  'con_forecast_c2_stk', 'con_forecast_c3_cgb_stk', 'con_forecast_c3_stk', 'con_forecast_cb_stk', 
                  'researcher_info', 't_author_honor']
    
    b_list3 = ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 't_author_honor',
                    'i_organ_score', 'gg_org_list', 't_great_author', 'author_pjhb']
    
    for table in b_list:
        print(table)
        if table in b_list3:
            continue
        if table == 'con_forecast_stk':
            path1 = '/data/group/800080/warehouse/prod/FCD/CHINA_STOCK/DAILY/SUNTIME/FCD_CHINA_STOCK_DAILY_SUNTIME.h5'    
            path2 = '/data/group/800080/warehouse/insample/FCD/CHINA_STOCK/DAILY/SUNTIME/FCD_CHINA_STOCK_DAILY_SUNTIME.h5'    
            root = '/data/group/800080/warehouse/insample/FCD/CHINA_STOCK/DAILY/SUNTIME'
        else:
            path1 = '/data/group/800080/warehouse/prod/DATABASE/SUNTIME/' + table + '/' + table + '.h5'
            path2 = '/data/group/800080/warehouse/insample/DATABASE/SUNTIME/' + table + '/' + table + '.h5'
            root = '/data/group/800080/warehouse/insample/DATABASE/SUNTIME/' + table
        dataset_name = table 
        if not os.path.exists(root):
            os.makedirs(root)
            
        with pd.HDFStore(path2) as h5_store:
            dat = IO.read_data([sdate,edate],alt=path1)
            if dataset_name in list(h5_store.root._v_groups.keys()):
                dt_lst = list(set(h5_store.select_column(dataset_name, 'dt')))
            else:
                dt_lst = []
            
            if append is True:
                cur_date_list = list(set(dat.index.get_level_values('dt')))
                for curr_date in cur_date_list:
                    
                    if curr_date in dt_lst:
                        print('csv2h5: exist: %s'%(curr_date))
                        dummy_id = h5_store.remove(dataset_name,'dt=curr_date')
                        print('csv2h5: removed: %s'%(curr_date))
            h5_store.append(dataset_name,dat,data_columns=True)

def get_date():
    fdate_list_dt = IO.read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    fdate_list.sort()
    df = IO.read_data([20190101,20220101],alt='/data/group/800080/warehouse/insample/DATABASE/WIND/AShareEODPrices/AShareEODPrices.h5')
    df.reset_index(inplace=True)
    date_list = list(set(df['dt']))
    date_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in date_list]
    date_list.sort()
    last_date = date_list[-1]
    idx = fdate_list.index(last_date)
    return fdate_list[idx+1], fdate_list[idx+5]

if __name__ =='__main__':

    sdate,edate = get_date()
    print(sdate,edate)
    RDF_daily(sdate,edate,operation='append')
    b_tables(sdate,edate,append=True)
    h5_trans(sdate,edate,append_flag=True)
