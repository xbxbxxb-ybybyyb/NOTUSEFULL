from enum import Enum,unique
@unique
class DType(Enum):
    STOCK=1
    FUTURES=2
    SPOT=3
    INDEX=4
@unique
class DFreq(Enum):
    TICK=1
    MINUTE=2
    DAILY=3
    WEEKLY=4
    QUARTERLY=5
    MONTHLY=6
    YEARLY=7
@unique
class DSource(Enum):
    HTSC                               = 1
    WIND                               = 2
    OPTM                               = 3
    SUNTIME                            = 4
    STYLEFACTOR                        = 5
    DERIVED                            = 6
    MAIN                               = 7
    SECONDMAIN                         = 8
    STYLEFACTOR2                       = 9
    DESCRIPTOR                         = 10
    CSI                                = 11

@unique
class UniType(Enum):
    HS300=1
    ZZ500=2
    SZ50=3
@unique
class MktType(Enum):
    CHINA=1
    HK=2
    US=3
@unique
class FType(Enum):
    FDD                                = 1 # Fundamental Data
    MD                                 = 2 # Market Data
    FCD                                = 3 # Forcast Data
    FACTOR                             = 4 # Factor Data
    ALPHA                              = 5 # Alpha Factor
    RISK                               = 6 # Risk Factor
    UNIV                               = 7 # Universe Data
    INDUSTRY                           = 8 # Industry Data
    CALENDAR                           = 9 # Calendar Data
    INDEXWEIGHT                        = 10
    VD                                 = 11

@unique
class DTable(Enum):
    # WIND Tables
    Ashareeoddindicator           = 1
    AShareFinancialIndicator      = 2
    AShareProfitExpress           = 3
    AShareProfitNotice            = 4
    AShareTTMHis                  = 5
    AShareBalanceSheet            = 6
    AShareCashFlow                = 7
    AShareIncome                  = 8
    AshareintensitytrendADJ       = 9
    AShareEnergyindexADJ          = 10
    AShareTechIndicators          = 11
    AShareL2Indicators            = 12
    AShareMoneyFlow               = 13
    htzqedbdzzbs                  = 14
    AShareEODDerivativeIndicator  = 15
    AShareIPO                     = 16
    AShareCompRestricted          = 17
    AShareSEO                     = 18
    AShareRightIssue              = 19
    ASharePledgeproportion        = 20
    AShareMjrHolderTrade          = 21
    AShareMarginTradeSum          = 22
    AShareStaff                   = 23
    AIndexWindIndustriesEOD       = 24
    # SUNTIME Tables
    cmb_report_research        = 101
    cmb_report_adjust          = 102
    cmb_report_subtable        = 103
    author_core_type           = 104
    der_report_research        = 105
    i_organ_score              = 106
    con_stock_deviation2       = 107
    stock_order2               = 108
    stock_diversity            = 109
    report_author              = 110
    stock_emotion              = 111
    con_stock_deviation        = 112
    stock_order3               = 113
    con_forecast_c3_cgb_stk    = 114
    der_report_subtable        = 115
    author_pjhb                = 116
    con_forecast_c2_stk        = 117
    researcher_info            = 118
    con_stock_deviation3       = 119
    con_forecast_cb_stk        = 120
    t_great_author             = 121
    gg_org_list                = 122
    stock_concern_level        = 123
    stock_report_adjustment    = 124
    author_pj                  = 125
    fcd_china_stock_daily_htsc = 126
    i_report_type              = 127
    stock_report_adjustment2   = 128
    stock_report_number        = 129
    con_forecast_c3_stk        = 130
    stock_report_extremum      = 131
    con_forecast_schedule      = 132
    author_core                = 133
    cmb_report_score_adjust    = 134
    t_author_honor             = 135
    # Others
    DERIVED_minute_block        = 201
    DERIVED_technical_indicator = 202
    DERIVED_barra_descriptor    = 203
    DERIVED_custom_descriptor   = 204
    DERIVED_barra               = 205
    DERIVED_market_base         = 206

    # WIND API
    APIDAILY                    = 301
    APIQUARTERLY                = 302