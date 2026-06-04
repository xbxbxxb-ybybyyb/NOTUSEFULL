
generate_pf_data_path = '/data/user/012620/generate_pf_data/'
pool_stock_path = '/data/user/011477/order/O32/pool/'
reb_path = '/data/user/012620/order/Rebalance_file/'
open_path = '/data/user/013547/建仓权重文件/'
o32_path='/data/user/011477/order/O32/'
data_center_path = '/data/group/800020/AlphaDataCenter/'
basic_data_path = data_center_path+'Basic/'
order_path = '/data/user/012620/order/'
valid_stock_path='/data/group/800020/AlphaTask/valid_stock/valid_stock/'
task_path = '/data/group/800020/AlphaTask/'
universe_path='/data/group/800020/AlphaDataCenter/PoolManagement/'
tools_path='/data/group/800020/AlphaTools/'
transit_path = '/data/group/800020/AlphaDataCenter/Transit/'
hfactor_path = '/data/group/800020/AlphaDataCenter/HFactor/'

depart_sample_path = '/data/group/800020/AlphaDataCenter/Department/DepartSample/'
parquet_path = '/data/user/015518/quant_data/qualified_factor/x_day_lib/latest/'
model_root_path = '/data/group/800020/AlphaDataCenter/Department/'
fix_1300_pkl_path = '/data/user/015623/FactorFactory/PICKLE/'
minute_trade_price_path = '/data/group/800020/AlphaDataCenter/minute_trade_price/'

sample_raw_path = data_center_path+'Sample/RawSample/'
sample_norm_path = data_center_path+'Sample/NormSample/'
hsample_raw_path = data_center_path+'HFSample/RawSample/'
hsample_norm_path = data_center_path+'HFSample/NormSample/'
basic_daily_path = data_center_path+'Basic/daily/'
minute_data_path = data_center_path+'Basic/minute/'
factor_data_path = data_center_path+'Factor/daily/'
hfactor_data_path = data_center_path+'HFactor/one_pm/'
fund_factor_data_path = data_center_path+'Factor/fundamental_tmp/'

day_depart_feature_path = depart_sample_path+'Sample/feature/'
day_depart_label_path = depart_sample_path+'Sample/label/'
fix_depart_feature_path = depart_sample_path+'HFSample/feature/'
fix_depart_label_path = depart_sample_path+'HFSample/label/'


factor_list_path = data_center_path+'Sample/factor_list.pkl'
hfactor_list_path = data_center_path+'HFSample/hfactor_list.pkl'
factor_info_path = depart_sample_path+'factor_info_shipan.pkl'
factor_info_path_tmp = depart_sample_path+'factor_info_tmp.pkl'
act_path = model_root_path+'DailyPrediction/'
model_path = model_root_path+'Models/'
weight_path = model_root_path+'DailyWeight/'
prediction_path = model_root_path+'DailyPrediction/'
DepSample_path = depart_sample_path
TeamSample_path = data_center_path




name_map={'0930':'am','1300':'pm','0930vwap':'vwap'}
model_config_dict = {
            'am':[
                ('XgboostRegression','am','0930_1129_norm_re_5d',5,240),
                ('LinearRegression','am','0930_1129_re_5d',5,240),
                ('DeepFM_Model','am','0930_1129_norm_re_5d',5,240)],
            'pm':[
                ('XgboostReg_Model_V1','pm','1300_1459_norm_re_5d',5,240),
                ('LinearRegression','pm','1300_1459_re_5d',5,240),
                ('DeepFM_Model','pm','1300_1459_norm_re_5d',5,240)],
            'vwap':[
                ('XgboostRegression','vwap','vwap_norm_re_5d',5,240),
                ('LinearRegression','vwap','vwap_re_5d',5,240),
                ('DeepFM_Model','vwap','vwap_re_norm_5d',5,240)]
            }
model_name_map_500 = {k:[m[0]+'_'+m[2] for m in v] for k,v in model_config_dict.items()}
model_name_map_300 = {k:[m[0]+'_'+m[2] for m in v] for k,v in model_config_dict.items()}
model_name_map={'500':model_name_map_500,'300':model_name_map_300}
update_params={'5160503':\
{'label_open':True,'label_update':True,'mode_portfolio':1,\
'transaction_time':'0930vwap','captial_fake':80e7,'open_capital':80e7,\
'add_capital':30e7,'mode_open':1,'contact':'IC2009','benchmark':'500',\
'name':'QuantMachine500'},\
'5160803':\
{'label_open':True,'label_update':True,'mode_portfolio':1,\
'transaction_time':'0930','captial_fake':80e7,'open_capital':80e7,\
'add_capital':50e7,'mode_open':1,'contact':'IC2009','benchmark':'500',\
'name':'AlphaHunter500'},\
'5160304':\
{'label_open':False,'label_update':True,'mode_portfolio':1,\
'transaction_time':'0930vwap','captial_fake':40e7,'open_capital':40e7,\
'add_capital':20e7,'mode_open':1,'contact':'IF2009','benchmark':'300',\
'name':'QuantMachine300'}}
