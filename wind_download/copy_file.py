import shutil
import os
from loguru import logger

h5_list = [
    # "DATABASE/WIND/AShareBalanceSheet/AShareBalanceSheet.h5",
    # "DATABASE/WIND/AShareST/AShareST.h5",
    # "DATABASE/WIND/AIndexMembers/AIndexMembers.h5",
    # "DATABASE/WIND/AShareConseption/AShareConseption.h5",
    # "DATABASE/WIND/AShareCashFlow/AShareCashFlow.h5",
    # "DATABASE/WIND/AShareIncome/AShareIncome.h5",
    # "DATABASE/WIND/AShareProfitExpress/AShareProfitExpress.h5",
    # "DATABASE/WIND/AShareProfitNotice/AShareProfitNotice.h5",
    # "DATABASE/WIND/AShareFinancialIndicator/AShareFinancialIndicator.h5",
    # "DATABASE/WIND/AShareTTMHis/AShareTTMHis.h5",
    # "DATABASE/WIND/AShareDividend/AShareDividend.h5",
    # "DATABASE/WIND/AShareDescription/AShareDescription.h5",
    # "DATABASE/WIND/AShareIndustriesClassCITICS/AShareIndustriesClassCITICS.h5",
    # "DATABASE/WIND/AShareInsideHolder/AShareInsideHolder.h5",
    # "DATABASE/WIND/AShareEODDerivativeIndicator/AShareEODDerivativeIndicator.h5",
    # "DATABASE/WIND/AShareEODPrices/AShareEODPrices.h5",
    # "DATABASE/WIND/AIndexEODPrices/AIndexEODPrices.h5",
    # "DATABASE/WIND/AShareManagementHoldReward/AShareManagementHoldReward.h5",
    # "DATABASE/WIND/AShareMoneyFlow/AShareMoneyFlow.h5",
    # "DATABASE/WIND/AShareL2Indicators/AShareL2Indicators.h5",
    # "DATABASE/WIND/AShareInsideHolder/AShareInsideHolder.h5",
    # "DATABASE/WIND/AShareIssuingDatePredict/AShareIssuingDatePredict.h5",
    #
    # "ETC/CHINA_STOCK/WIND/ETC_CHINA_STOCK_WIND.h5",
    # "MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5",
    # "MD/CHINA_INDEX/DAILY/WIND/MD_CHINA_INDEX_DAILY_WIND.h5",
    # "INDUSTRY/CHINA_STOCK/DAILY/WIND/INDUSTRY_CHINA_STOCK_DAILY_WIND.h5",
    # "FDD/CHINA_STOCK/DAILY/WIND/FDD_CHINA_STOCK_DAILY_WIND.h5",
    # "FDD/CHINA_STOCK/QUARTERLY/WIND/FDD_CHINA_STOCK_QUARTERLY_WIND.h5",
    # "UNIV/CHINA_STOCK/DAILY/OPTM/UNIV_CHINA_STOCK_DAILY_OPTM.h5",
    # "RISK/CHINA_STOCK/DAILY/STYLEFACTOR/RISK_CHINA_STOCK_DAILY_STYLEFACTOR.h5",

    # "FCD/CHINA_STOCK/DAILY/SUNTIME/FCD_CHINA_STOCK_DAILY_SUNTIME.h5",
    # "CALENDAR/CHINA_STOCK/DAILY/HTSC/CALENDAR_CHINA_STOCK_DAILY_HTSC.h5",
    # "LOCAL_DATA/CSV/stock_universe/universe_complete.h5",


    "DATABASE/SUNTIME/stock_concern_level/stock_concern_level.h5",
    "DATABASE/SUNTIME/author_pj/author_pj.h5",
    "DATABASE/SUNTIME/CON_FORECAST_C3_IDX/CON_FORECAST_C3_IDX.h5",
    "DATABASE/SUNTIME/con_forecast_schedule/con_forecast_schedule.h5",
    "DATABASE/SUNTIME/gg_org_list/gg_org_list.h5",
    "DATABASE/SUNTIME/cmb_report_subtable/cmb_report_subtable.h5",
    "DATABASE/SUNTIME/con_stock_deviation2/con_stock_deviation2.h5",
    "DATABASE/SUNTIME/CON_FORECAST_C2_IDX/CON_FORECAST_C2_IDX.h5",
    "DATABASE/SUNTIME/author_core/author_core.h5",
    "DATABASE/SUNTIME/con_forecast_cb_stk/con_forecast_cb_stk.h5",
    "DATABASE/SUNTIME/der_report_subtable/der_report_subtable.h5",
    "DATABASE/SUNTIME/cmb_report_adjust/cmb_report_adjust.h5",
    "DATABASE/SUNTIME/cmb_report_score_adjust/cmb_report_score_adjust.h5",
    "DATABASE/SUNTIME/CON_FORECAST_IDX/CON_FORECAST_IDX.h5",
    "DATABASE/SUNTIME/i_report_type/i_report_type.h5",
    "DATABASE/SUNTIME/stock_report_extremum/stock_report_extremum.h5",
    "DATABASE/SUNTIME/author_pjhb/author_pjhb.h5",
    "DATABASE/SUNTIME/t_great_author/t_great_author.h5",
    "DATABASE/SUNTIME/con_forecast_c3_cgb_stk/con_forecast_c3_cgb_stk.h5",
    "DATABASE/SUNTIME/t_author_honor/t_author_honor.h5",
    "DATABASE/SUNTIME/report_author/report_author.h5",
    "DATABASE/SUNTIME/con_forecast_c3_stk/con_forecast_c3_stk.h5",
    "DATABASE/SUNTIME/author_core_type/author_core_type.h5",
    "DATABASE/SUNTIME/stock_report_adjustment/stock_report_adjustment.h5",
    "DATABASE/SUNTIME/con_stock_deviation3/con_stock_deviation3.h5",
    "DATABASE/SUNTIME/researcher_info/researcher_info.h5",
    "DATABASE/SUNTIME/stock_order3/stock_order3.h5",
    "DATABASE/SUNTIME/stock_report_adjustment2/stock_report_adjustment2.h5",
    "DATABASE/SUNTIME/i_organ_score/i_organ_score.h5",
    "DATABASE/SUNTIME/stock_order2/stock_order2.h5",
    "DATABASE/SUNTIME/stock_emotion/stock_emotion.h5",
    "DATABASE/SUNTIME/con_forecast_c2_stk/con_forecast_c2_stk.h5",
    "DATABASE/SUNTIME/stock_report_number/stock_report_number.h5",
    "DATABASE/SUNTIME/stock_diversity/stock_diversity.h5",
    "DATABASE/SUNTIME/con_stock_deviation/con_stock_deviation.h5",





]
#
# source_folder = "/data/group/800080/warehouse/prod/"
# destination_folder = "/data/group/800002/basic_data/full/financial_data"
#
# total_size = 0
# for file in h5_list:
#     source_file = os.path.join(source_folder, file)
#     tmp_folder = destination_folder
#     for i in file.split("/")[:-1]:
#         tmp_folder = os.path.join(tmp_folder, i)
#         if not os.path.exists(tmp_folder):
#             os.mkdir(tmp_folder)
#     destination_file = os.path.join(destination_folder, file)
#     size = os.path.getsize(source_file) / 1000 / 1000
#     total_size += size
#     logger.info("file={}, size={}".format(source_file, int(size)))
#     shutil.copyfile(source_file, destination_file)
#
# logger.info("total_size={}".format(total_size))
