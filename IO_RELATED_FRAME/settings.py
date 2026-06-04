import os

# TODO 对于研究人员，只需要切换BASE_DIR，即可以调整至样本内数据集，在此数据集上做因子开发
BASE_DIR = "/data/group/800080"
BASE_DIR2 = "/data/group/800002/basic_data/full"

# 以下配置业务人员不需要修改

#DAILY_DATA_PATH = os.path.join(BASE_DIR, "Apollo/AlphaDataBase")
DAILY_DATA_PATH = os.path.join(BASE_DIR2, "daily_data")

#MINUTE_DATA_PATH = os.path.join(BASE_DIR, "PanelMinDataForZT")
MINUTE_DATA_PATH = os.path.join(BASE_DIR2, "minute_data")


H5_DATA_PATH = os.path.join(BASE_DIR2, "financial_data")

ALPHA_BASE_DIR = "/data/group/800002/alpha_factor"

LIB_BASE_DIR = os.path.join(ALPHA_BASE_DIR, "lib")

X_NONFACTOR_LIB = os.path.join(LIB_BASE_DIR, "x_nonfactor_lib")

X_FACTOR_LIB = os.path.join(LIB_BASE_DIR, "x_factor_lib")

X_FACTOR_LIB_BAK = os.path.join(LIB_BASE_DIR, "x_factor_lib_bak")

# FACTOR_LIB_BAK = "/data/group/800002/alpha_factor_back_up"

FACTOR_LIB_BAK = "/arch0/group/800502/factor_bak"

H5_DATA_BAK = "/arch0/group/800502/H5_bak"

X_FACTOR_LIB_SUBSET1 = os.path.join(LIB_BASE_DIR, "x_factor_lib_subset_1")

VALID_FACTOR_LIB = os.path.join(LIB_BASE_DIR, "valid_factor_lib")

TMP_FACTOR_LIB = os.path.join(LIB_BASE_DIR, "tmp_factor_lib")

LOG_PATH = os.path.join(ALPHA_BASE_DIR, "log")

TEST_PATH = os.path.join(ALPHA_BASE_DIR, "test")

H5_FILE_FILTER_MAPPING = {
    'WIND_AShareBalanceSheet': 'ANN_DT',
    'WIND_AShareCashFlow': 'ANN_DT',
    'WIND_AShareIncome': 'ANN_DT',
    'WIND_AShareProfitExpress': 'ANN_DT',
    'WIND_AShareProfitNotice': 'S_PROFITNOTICE_DATE',
    'WIND_AShareFinancialIndicator': 'ANN_DT',
    'WIND_AShareTTMHis': 'ANN_DT',
    'WIND_AShareANNFinancialIndicator': 'ANN_DT',
    'WIND_AShareIssuingDatePredict': 'ANN_DT',
    'WIND_AShareDividend': 'HTSC_DATE',
    'WIND_AIndexFinancialderivative': 'OPDATE',
    'FDD_CHINA_STOCK_QUARTERLY_WIND': 'stm_issuingdate',
    'WIND_FinNotesDetail': 'OPDATE',
    'WIND_AShareIBrokerIndicator': 'ANN_DT',
    'WIND_AShareInsuranceIndicator': 'ANN_DT',
    'WIND_AShareBankIndicator': 'ANN_DT',
    'WIND_Top5ByLongTermBorrowing': 'ANN_DT',
    'WIND_AshareOtherreceivables': 'OPDATE',
    'WIND_AShareFinancialExpense': 'ANN_DT',
    'WIND_AshareInventorydetails': 'OPDATE',
    'WIND_AshareFinancialaccounts': 'ANN_DT',
    'WIND_Top5ByAccountsReceivable': 'OPDATE',
    'WIND_AShareAuditOpinion': 'ANN_DT',
    'WIND_AShareSalesSegment': 'OPDATE',
    'WIND_Top5ByOperatingIncome': 'ANN_DT',
    'SUNTIME_con_forecast_schedule': 'ENTRYDATE',
    'SUNTIME_stock_order3': 'ENTRYDATE',
    'SUNTIME_stock_report_adjustment': 'ENTRYDATE',
    'SUNTIME_stock_report_number': 'ENTRYDATE',
    'SUNTIME_stock_order2': 'ENTRYDATE',
    'SUNTIME_stock_report_adjustment2': 'ENTRYDATE',
    'SUNTIME_stock_concern_level': 'ENTRYDATE',
    'SUNTIME_con_stock_deviation3': 'ENTRYDATE',
    'SUNTIME_con_stock_deviation2': 'ENTRYDATE',
    'SUNTIME_con_stock_deviation': 'ENTRYDATE',
    'SUNTIME_stock_diversity': 'ENTRYDATE',
    'SUNTIME_stock_emotion': 'ENTRYDATE',
    'SUNTIME_stock_report_extremum': 'ENTRYDATE',
    'SUNTIME_con_forecast_c2_stk': 'ENTRYDATE',
    'SUNTIME_con_forecast_c3_cgb_stk': 'ENTRYDATE',
    'SUNTIME_con_forecast_c3_stk': 'ENTRYDATE',
    'SUNTIME_con_forecast_cb_stk': 'ENTRYDATE',
    'SUNTIME_CON_FORECAST_IDX': 'ENTRYDATE',
    'SUNTIME_CON_FORECAST_C2_IDX': 'ENTRYDATE',
    'SUNTIME_CON_FORECAST_C3_IDX': 'ENTRYDATE',
    'FCD_CHINA_STOCK_DAILY_SUNTIME': 'ENTRYDATE',
    'WIND_AshareAgingstructure': 'OPDATE',
    'WIND_AshareOtherAccountsreceivable': 'OPDATE',
    'WIND_AShareDevaluationPreparation': 'ANN_DT',
    'WIND_AShareFixedAssets': 'ANN_DT',
    'WIND_AShareLTPrepaidEXP': 'ANN_DT',
    'WIND_AShareIntangibleAssets': 'ANN_DT',
    'WIND_AShareDeferredTaxAssets': 'ANN_DT',
    'WIND_AShareDeferredTaxLiability': 'ANN_DT',
    'WIND_AShareIncomeTax': 'ANN_DT',
    'CHARACTERISTIC_shhknorthward': 'HTSC_DATE',
    'SUNTIME_der_excess_stock': 'HTSC_DATE',
    'SUNTIME_cmb_report_research': 'HTSC_DATE',
    'SUNTIME_cmb_report_subtable': 'HTSC_DATE',
    'WIND_AShareMarginTrade': 'HTSC_DATE',
    'WIND_SHSCChannelholdings': 'HTSC_DATE',
    'CHARACTERISTIC_fnd_secuportfolio': 'HTSC_DATE',
    'WIND_AShareManagementHoldReward': 'HTSC_DATE',
    #NSW
    'WIND_AShareStaff':'ANN_DT',
    'WIND_AShareStaffStructure':'ANN_DT',
    'WIND_AshareISActivity':'ANN_DT',
    'WIND_AShareinstHolderDerData':'ANN_DATE',
    'WIND_AShareManagement':'ANN_DATE',
    'WIND_AShareIncDescription':'ANN_DT',
    'WIND_AShareISParticipant':'OPDATE'
}

H5_FILES_FILTER_UNTIL_TODAY = ['WIND_AShareIndustriesClassCITICS', 'WIND_AShareDescription',
                               'WIND_AShareIndustriesCode',
                               'WIND_AShareST',
                               'WIND_AShareCapitalization', 'WIND_AShareFreeFloat', 'WIND_AShareIPO',
                               'WIND_AShareAgency',
                               'WIND_AShareCOCapitaloperation', 'WIND_ASharePledgepro', 'WIND_AshareStockRepo',
                               'WIND_AShareCorporateFinance',
                               'WIND_AShareIssueCommAudit', 'WIND_AShareEquityDivision', 
                               'WIND_IPOCompRFA', 'WIND_IECMemberList', 'WIND_AShareLeadUnderwriter',
                               'WIND_AShareRightIssue', 'WIND_AShareSEO', 'WIND_IPOInquiryDetails',
                               'WIND_AShareIncQuantityPrice',
                               'WIND_AShareIncQuantityDetails',
                               'WIND_AShareIncExercisePct', 'WIND_AShareIncExecQtyPri', 'WIND_AShareEsopDescription',
                               'WIND_AShareEsopTradingInfo',
                               'WIND_AShareMajorHolderPlanHold', 'WIND_AShareTypeCode',
                               'WIND_htzqedbdzzbs',
                               'WIND_AShareMainandnoteitems', 'WIND_AIndexMembers', 'WIND_AShareConseption'
                               ]

H5_FILES_NO_FILTER = {'ETC_CHINA_STOCK_WIND': ["stock"],
                      'CALENDAR_CHINA_STOCK_DAILY_HTSC': ["date", "stock"]}
