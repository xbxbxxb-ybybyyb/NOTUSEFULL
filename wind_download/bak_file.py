import shutil
import os
import datetime
from loguru import logger


h5_list = [
    "DATABASE/WIND/AShareBalanceSheet/AShareBalanceSheet.h5",
    "DATABASE/WIND/AShareST/AShareST.h5",
    "DATABASE/WIND/AIndexMembers/AIndexMembers.h5",
    "DATABASE/WIND/AShareConseption/AShareConseption.h5",
    "DATABASE/WIND/AShareCashFlow/AShareCashFlow.h5",
    "DATABASE/WIND/AShareIncome/AShareIncome.h5",
    "DATABASE/WIND/AShareProfitExpress/AShareProfitExpress.h5",
    "DATABASE/WIND/AShareProfitNotice/AShareProfitNotice.h5",
    "DATABASE/WIND/AShareFinancialIndicator/AShareFinancialIndicator.h5",
    "DATABASE/WIND/AShareTTMHis/AShareTTMHis.h5",
    "DATABASE/WIND/AShareDividend/AShareDividend.h5",
    "DATABASE/WIND/AShareDescription/AShareDescription.h5",
    "DATABASE/WIND/AShareIndustriesClassCITICS/AShareIndustriesClassCITICS.h5",
    "DATABASE/WIND/AShareInsideHolder/AShareInsideHolder.h5",
    "DATABASE/WIND/AShareEODDerivativeIndicator/AShareEODDerivativeIndicator.h5",
    "DATABASE/WIND/AShareEODPrices/AShareEODPrices.h5",
    "DATABASE/WIND/AIndexEODPrices/AIndexEODPrices.h5",
    "DATABASE/WIND/AShareManagementHoldReward/AShareManagementHoldReward.h5",
    "DATABASE/WIND/AShareMoneyFlow/AShareMoneyFlow.h5",
    "DATABASE/WIND/AShareL2Indicators/AShareL2Indicators.h5",
    "DATABASE/WIND/AShareInsideHolder/AShareInsideHolder.h5",
    "DATABASE/WIND/AShareIssuingDatePredict/AShareIssuingDatePredict.h5",

    "ETC/CHINA_STOCK/WIND/ETC_CHINA_STOCK_WIND.h5",
    "MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5",
    "MD/CHINA_INDEX/DAILY/WIND/MD_CHINA_INDEX_DAILY_WIND.h5",
    "INDUSTRY/CHINA_STOCK/DAILY/WIND/INDUSTRY_CHINA_STOCK_DAILY_WIND.h5",
    "FDD/CHINA_STOCK/DAILY/WIND/FDD_CHINA_STOCK_DAILY_WIND.h5",
    "FDD/CHINA_STOCK/QUARTERLY/WIND/FDD_CHINA_STOCK_QUARTERLY_WIND.h5",
    "UNIV/CHINA_STOCK/DAILY/OPTM/UNIV_CHINA_STOCK_DAILY_OPTM.h5",
    "RISK/CHINA_STOCK/DAILY/STYLEFACTOR/RISK_CHINA_STOCK_DAILY_STYLEFACTOR.h5",

    "FCD/CHINA_STOCK/DAILY/SUNTIME/FCD_CHINA_STOCK_DAILY_SUNTIME.h5",
    "CALENDAR/CHINA_STOCK/DAILY/HTSC/CALENDAR_CHINA_STOCK_DAILY_HTSC.h5"
]

source_folder = "/data/group/800080/warehouse/prod/"
today = datetime.date.today()
destination_folder = "/arch0/group/800445/wind_h5_bak/{}".format(today)


total_size = 0
for file in h5_list:
    source_file = os.path.join(source_folder, file)
    tmp_folder = destination_folder
    for i in file.split("/")[:-1]:
        tmp_folder = os.path.join(tmp_folder, i)
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
    destination_file = os.path.join(destination_folder, file)
    size = os.path.getsize(source_file) / 1000 / 1000
    total_size += size
    logger.info("file={}, size={}".format(source_file, int(size)))
    shutil.copyfile(source_file, destination_file)

logger.info("total_size={}".format(total_size))





