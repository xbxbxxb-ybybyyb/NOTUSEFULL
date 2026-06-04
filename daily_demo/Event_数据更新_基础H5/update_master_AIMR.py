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
import json
from link import LinkMessage
from xquant.compute.aimr import AIMR
linkins = LinkMessage()

#返回交易日的，缺省值nan，返回当天
sdate,edate,_= check_update_date()

sdate = 20240402
edate = 20240402

#print(sdate,edate)
linkins.sendMessage('[INFO][金工-数据下载]原始wind数据开始下载')
flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
if not os.path.exists(flag_root):
    os.makedirs(flag_root)


flag_path1 = flag_root + str(edate) + '_' + 'RDF.start'
with open(flag_path1,'w') as file:
    pass 

sdate, edate, cdate_list = check_update_date(sdate=sdate, edate=edate)
#WIND_AShareBalanceSheet
qtr_list = [
            'WIND_AShareCashFlow', 'WIND_AShareIncome', 'WIND_AShareBalanceSheet', 'WIND_AShareProfitExpress',
            'WIND_AShareProfitNotice', 'WIND_AShareFinancialIndicator', 
            'WIND_AShareTTMHis',
            'WIND_AShareANNFinancialIndicator',
            'WIND_AShareIssuingDatePredict', 'WIND_AShareDividend', 'WIND_AIndexFinancialderivative'
            ]

first_daily_list = [
                    'WIND_AShareDescription', 'WIND_AShareIndustriesClassCITICS', 'WIND_AShareST',
                    # 220701 下线asharemanagement
                    #'WIND_AShareManagement',
                    'WIND_AShareMonthlyReportsofBrokers', 'WIND_AShareEODDerivativeIndicator',
                    'WIND_AShareEODPrices', 'WIND_AIndexEODPrices', 'WIND_AIndexValuation',
                    'WIND_AShareManagementHoldReward', 'WIND_AShareMoneyFlow',
                    'WIND_AShareL2Indicators', 'WIND_AIndexMembers', 'WIND_AShareConseption'
                    ]


table_dict = {'QUARTERLY': qtr_list, 'DAILY': first_daily_list}

param_list = []

par1 = ['WIND_AShareFinancialIndicator', 'WIND_AShareDescription', 'WIND_AIndexEODPrices', 'WIND_AShareConseption',
        'WIND_AShareMoneyFlow', 'WIND_AShareIssuingDatePredict', 'WIND_AShareEODDerivativeIndicator', 'WIND_AShareEODPrices']
        
par2 = ['WIND_AIndexFinancialderivative', 'WIND_AShareDividend',
        'WIND_AShareANNFinancialIndicator', 'WIND_AIndexValuation', 'WIND_AShareIncome',
        'WIND_AShareCashFlow']
        
par3 = ['WIND_AIndexMembers', 'WIND_AShareProfitNotice', 'WIND_AShareTTMHis', 'WIND_AShareL2Indicators', 'WIND_AShareProfitExpress',
        'WIND_AShareST', 'WIND_AShareMonthlyReportsofBrokers', 'WIND_AShareIndustriesClassCITICS', 'WIND_AShareBalanceSheet', 'WIND_AShareManagementHoldReward']


    

param_list.append("{};{};{};{};{}".format(",".join(par1),sdate,edate,'/data/group/800080/warehouse/prod/','append'))
param_list.append("{};{};{};{};{}".format(",".join(par2),sdate,edate,'/data/group/800080/warehouse/prod/','append'))
param_list.append("{};{};{};{};{}".format(",".join(par3),sdate,edate,'/data/group/800080/warehouse/prod/','append'))



params = {
        "parallel_list": param_list,
        "tag": "xquant",
        "cpu": 3,
        "gpu": 0,
        "memory": 10240,
        "preferred_gpu": 0
    }
AIMR.runTasks('update_wind_htsc_AIMR.py', json.dumps(params))

    
    
    
    
#flag_path1 = flag_root + str(edate) + '_' + 'RDF.success'
#with open(flag_path1,'w') as file:
#    pass 
#linkins.sendMessage('[INFO][金工-数据下载]原始wind数据下载完成')
    