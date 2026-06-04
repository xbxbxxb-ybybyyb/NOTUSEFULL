import pandas as pd
import os
from loguru import logger
from pandas.testing import  assert_frame_equal
import datetime

wind_path_now ="/data/group/800080/warehouse/prod/DATABASE/WIND"
wind_path_new ="/data/group/800120/basic_data/full/financial_data/DATABASE/WIND"

today=datetime.datetime.now()
twodays =datetime.timedelta(days=2)
destdays = today-twodays

qtr_list = ['AShareBalanceSheet', 'AShareCashFlow', 'AShareIncome', 'AShareProfitExpress',
            'AShareProfitNotice', 'AShareFinancialIndicator', 'AShareTTMHis',
            'AShareANNFinancialIndicator',
            'AShareIssuingDatePredict', 'AShareDividend', 'AIndexFinancialderivative']

first_daily_list = ['AShareDescription', 'AShareIndustriesClassCITICS', 'AShareST',
                    'AShareManagement',
                    'AShareMonthlyReportsofBrokers', 'AShareEODDerivativeIndicator',
                    'AShareEODPrices', 'AIndexEODPrices', 'AIndexValuation',
                    'AShareManagementHoldReward', 'AShareMoneyFlow',
                    'AShareL2Indicators', 'AIndexMembers', 'AShareConseption']

finalList = qtr_list+first_daily_list


# for root,dirs,files in os.walk(wind_path_new):

for dir in finalList:

    try:
        data_now = pd.read_hdf(os.path.join(wind_path_now,dir,dir+".h5"))
        data_new = pd.read_hdf(os.path.join(wind_path_new,dir,dir+".h5"))
        last_now_time = data_now.index.values[-1][0]
        last_new_time = data_now.index.values[-1][0]

        if last_now_time == last_new_time:

            assert_frame_equal(data_now.loc[last_now_time],data_new.loc[last_now_time],check_frame_type=False)
            logger.info(" {}  data matched ".format(dir))

        else:
            # 如果新版数据不是最新的，生产上是更新的，
            if last_new_time< last_now_time:
                mtime =os.stat(os.path.join(wind_path_now,dir,dir+".h5")).st_mtime
                if mtime>destdays:
                    logger.info("{} 由其他脚本更新".format(dir))
                else:
                    logger.info("{} 数据最新一段时间未更新".format(dir))

    except Exception as e:

            logger.error("Exception : checkdir ={},reason={}".format(dir,e))


