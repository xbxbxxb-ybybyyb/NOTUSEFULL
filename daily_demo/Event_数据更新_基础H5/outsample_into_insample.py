from multifactor.IO import IO
import pandas as pd
import numpy as np
import time
import os
from concurrent.futures import ProcessPoolExecutor as Pool
from concurrent.futures import as_completed

def RDF_daily(sdate,edate,table_name,operation='create'):
    root1 = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    root2 = '/data/group/800080/warehouse/insample/DATABASE/WIND/'
    if not os.path.exists(root2 + table_name):
        os.makedirs(root2 + table_name)
    table_h5_file1 = root1 + table_name + '/' + table_name + '.h5'
    table_h5_file2 = root2 + table_name + '/' + table_name + '.h5'

    dataset_name = 'WIND_' + table_name

    with pd.HDFStore(table_h5_file2) as h5_store:

        dat = IO.read_data([sdate,edate],alt=table_h5_file1)
        if dataset_name in list(h5_store.root._v_groups.keys()):
            dt_lst = list(set(h5_store.select_column(dataset_name, 'dt')))
        else:
            dt_lst = []

        if operation == 'append':      
            curr_date = list(set(dat.index.get_level_values('dt')))[0]
            print (curr_date)
            if curr_date in dt_lst:
                print('csv2h5: exist: %s'%(curr_date))
                dummy_id = h5_store.remove(dataset_name,'dt=curr_date')
                print('csv2h5: append: %s'%(curr_date))

        h5_store.append(dataset_name,dat,data_columns=True)
        return table_name


def h5_trans(sdate,edate,path1,path2,operation='create'):
    df = IO.read_data([sdate,edate],alt=path1)
    for col in list(df.columns):
        print(col)
        df1 = df[[col]]
        IO.pd_hdf5_writer(df1, path2, dataset=col)





def table_daily(sdate,edate,path1,path2,dataset_name, operation='create'):

    with pd.HDFStore(path2) as h5_store:
        dat = IO.read_data([sdate,edate],alt=path1)

        h5_store.append(dataset_name,dat,data_columns=True)



if __name__ =='__main__':
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
                'WIND_AShareL2Indicators','WIND_AIndexMembers','WIND_AShareConseption']

    tech_daily_list = [ 'WIND_AShareTechIndicators', 'WIND_AshareintensitytrendADJ', 'WIND_AShareEnergyindexADJ','WIND_AShareswingReversetrendADJ']




    tic = time.time()

        
    b_list = ['con_forecast_stk', 'con_forecast_schedule','stock_order3','stock_report_adjustment',
                  'stock_report_number','stock_order2','stock_report_adjustment2','stock_concern_level',
                  'con_stock_deviation3','con_stock_deviation2','con_stock_deviation',
                  'stock_diversity','stock_emotion','stock_report_extremum',
                  'der_report_subtable', 'cmb_report_score_adjust', 'i_organ_score', 'report_author', 
                  'cmb_report_adjust', 'gg_org_list', 'i_report_type', 'author_core_type', 'author_core',
                  'cmb_report_subtable', 'author_pj', 'author_pjhb', 't_great_author',
                  'con_forecast_c2_stk', 'con_forecast_c3_cgb_stk', 'con_forecast_c3_stk', 'con_forecast_cb_stk', 
                  'researcher_info', 't_author_honor','der_report_research','cmb_report_research']
    
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
        table_daily(20000101,20190101,path1,path2,dataset_name)    
    toc = time.time()
    print(toc - tic)
    
    
    
    
    
    