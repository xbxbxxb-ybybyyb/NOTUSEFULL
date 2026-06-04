# -*- coding: utf-8 -*-
"""
# data update master
"""

import os
from multifactor.data.utils import *
from update_wind import update_wind, update_wind1
from updater_universe import updater_universe
from BarraRiskFactor_daily import update_risk_factor_daily
from update_wind_htsc import first_job
from update_wind_fin import update_wind_fin
from link import LinkMessage
linkins = LinkMessage()

#返回交易日的，缺省值nan，返回当天
sdate,edate,_= check_update_date()

print(sdate,edate)
flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
if not os.path.exists(flag_root):
    os.makedirs(flag_root)

RDF_root = flag_root + 'RDF/'

qtr_list = [
            'AShareCashFlow', 'AShareIncome', 'AShareBalanceSheet', 'AShareProfitExpress',
            'AShareProfitNotice', 'AShareFinancialIndicator', 
            'AShareTTMHis',
            'AShareANNFinancialIndicator',
            'AShareIssuingDatePredict', 'AShareDividend', 'AIndexFinancialderivative'
            ]

first_daily_list = [
                    'AShareDescription', 'AShareIndustriesClassCITICS', 'AShareST',
                    # 220701 下线asharemanagement
                    #'WIND_AShareManagement',
                    'AShareMonthlyReportsofBrokers', 'AShareEODDerivativeIndicator',
                    'AShareEODPrices', 'AIndexEODPrices', 'AIndexValuation',
                    'AShareManagementHoldReward', 'AShareMoneyFlow',
                    'AShareL2Indicators', 'AIndexMembers', 'AShareConseption'
                    ]

trial = 0

while trial < 5:

    success_cnt = 0

    for table in qtr_list + first_daily_list:
        table_flag = RDF_root + table + ".success"
        if not os.path.exists(table_flag):
            logger.error("[ERROR][金工-数据下载]RDF表格下载未完成, table={}".format(table))
            linkins.sendMessage("[ERROR][金工-数据下载]RDF表格下载未完成, table={}".format(table))
        else:
            success_cnt += 1
    
    if success_cnt == 24:
        flag_path1 = flag_root + str(edate) + '_' + 'RDF.success'
        with open(flag_path1,'w') as file:
            pass
        break
    else:
        sleep(120)



if os.path.exists(flag_root + str(edate) + '_' + 'RDF.success'):
    linkins.sendMessage('[INFO][金工-数据下载]原始wind数据下载完成')
        

    #价量数据和提取出来的财务数据
    linkins.sendMessage('[INFO][金工-数据下载]加工表开始计算')
    flag_path1 = flag_root + str(edate) + '_' + 'MD.start'
    with open(flag_path1,'w') as file:
        pass 


    update_wind(sdate,edate) #rdf_h5 to FDD_csv MD_csv to FDD_h5 MD_h5

    flag_path1 = flag_root + str(edate) + '_' + 'MD_ori.success'
    with open(flag_path1,'w') as file:
        pass 
        
    update_wind1(sdate,edate)

    linkins.sendMessage('[INFO][金工-数据下载]加工表计算完成')


    linkins.sendMessage('[INFO][金工-数据下载]Universe开始计算')
    flag_path1 = flag_root + str(edate) + '_' + 'UNIV.start'
    with open(flag_path1,'w') as file:
        pass 
    # NSW
    while not os.path.exists(os.path.join(flag_root,str(edate)+"_"+"MD.success")):
        time.sleep(60)
        print("wait for MD.success")
    updater_universe(sdate,edate) # rdf_h5 to universe to universe_csv to universe_h5
    flag_path1 = flag_root + str(edate) + '_' + 'UNIV.success'
    with open(flag_path1,'w') as file:
        pass 
    linkins.sendMessage('[INFO][金工-数据下载]Universe计算完成')
        


    # flag_path1 = flag_root + str(edate) + '_' + 'RISK.start'
    # with open(flag_path1,'w') as file:
        # pass   
    # update_risk_factor_daily(sdate,edate)
    # flag_path1 = flag_root + str(edate) + '_' + 'RISK.success'
    # with open(flag_path1,'w') as file:
        # pass 
        




    flag_path1 = flag_root + str(edate) + '_' + 'FDD.start'
    with open(flag_path1,'w') as file:
        pass 
    #update_wind_fin(sdate,edate) #windvip to windvip_csv to wind_vip_h5
    flag_path1 = flag_root + str(edate) + '_' + 'FDD.success'
    with open(flag_path1,'w') as file:
        pass 
else:
    raise RuntimeError("[ERROR][金工-数据下载]RDF表格下载未完成!!!")