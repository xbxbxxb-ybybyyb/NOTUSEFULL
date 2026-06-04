from xquant.thirdpartydata.factordata import FactorData
s = FactorData()


df1 = s.get_factor_value('GOGOAL_CON_FORECAST_C2_CI', factors=['S_INFO_WINDCODE', 'TRADE_DT', 'S_DQ_PRECLOSE', 'S_DQ_OPEN'], TRADE_DT=['>20180701', '<20180929'])
stocks = ["000001.SZ"]
#df1 = s.get_factor_value("ZXTL_md_institution", factors=["party_id", 'update_time'], UPDATE_TIME=['>20210604'], update_time=['2323'])


print(df1)


