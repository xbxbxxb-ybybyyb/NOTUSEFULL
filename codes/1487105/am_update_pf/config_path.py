#hpge
generate_pf_data_path = '/data/user/012620/generate_pf_data/'
# generate_pf_data_path = '/data/user/012620/AlphaDataCenter/Department/DailyWeight/Open_position/'
fix_dict_path = '/data/user/012620/AlphaDataCenter/Department/DepartSample/fix_dict.pkl'
pool_stock_path = '/data/user/011477/order/O32/pool/'
reb_path = '/data/user/012620/order/Rebalance_file/'
open_path = '/data/user/013547/建仓权重文件/'
o32_path='/data/user/011477/order/O32/' #@
#o32_path='/data/user/012620/order/O32/' #@
data_center_path = '/data/user/012620/AlphaDataCenter/'
basic_data_path = data_center_path+'Basic/'
basic_data_path_bk = '/data/user/015618/Share/013551/'
order_path = '/data/user/012620/order/'
code_root_path = '/data/user/012620/shipan/'
task_path = code_root_path+'AlphaTask/'
valid_stock_path=task_path+'/valid_stock/valid_stock/'
tools_path= code_root_path+'AlphaTools/'
factor_management_path = code_root_path+'Halpha/hf/'
universe_path='/data/user/012620/AlphaDataCenter/PoolManagement/'

transit_path = '/data/user/012620/AlphaDataCenter/Transit/'
hfactor_path = '/data/user/012620/AlphaDataCenter/HFactor/'

depart_sample_path = '/data/user/012620/AlphaDataCenter/Department/DepartSample/'
parquet_path = '/data/user/015518/quant_data/qualified_factor/x_day_lib/latest/'
model_root_path = '/data/user/012620/AlphaDataCenter/Department/'
depart_factors_path = '/data/group/800002/alpha_factor/lib/x_factor_lib/'
depart_factor_pool_path = '/data/group/800002/alpha_factor/lib/x_factor_lib/'
minute_trade_price_path = '/data/user/012620/AlphaDataCenter/minute_trade_price/'




sample_raw_path = data_center_path+'Sample/RawSample/'
sample_norm_path = data_center_path+'Sample/NormSample/'
hsample_raw_path = data_center_path+'HFSample/RawSample/'
hsample_norm_path = data_center_path+'HFSample/NormSample/'
basic_daily_path = data_center_path+'Basic/daily/'
minute_data_path = data_center_path+'Basic/minute/'
factor_data_path = data_center_path+'Factor/daily/'
hfactor_data_path = data_center_path+'HFactor/one_pm/'
fund_factor_data_path = data_center_path+'Factor/fundamental_tmp/'

factor_info_path_tmp = '/data/group/800469/AlphaDataCenter/Department/DepartSample/factor_info_nnnn.pkl'#@
factor_day_path_dict_path = '/data/user/012620/AlphaDataCenter/Department/DepartSample/factor_day_path_dict.pkl'#@
factor_fix_path_dict_path = '/data/user/012620/AlphaDataCenter/Department/DepartSample/factor_fix_path_dict.pkl'#@
factor_label_path_dict_path = '/data/user/012620/AlphaDataCenter/Department/DepartSample/factor_label_path_dict.pkl' #@
feature_fix_path = '/data/user/012620/AlphaDataCenter/Department/DepartSample/'
timepoint_list = ['0930','1000','1030','1100','1300','1330','1400','1430']

day_depart_feature_path = depart_sample_path+'Sample/feature/'
day_depart_label_path = depart_sample_path+'Sample/label/'
fix_depart_feature_path = depart_sample_path+'HFSample/feature/'
fix_depart_label_path = depart_sample_path+'HFSample/label/'

neu_factor_data_path = '/data/user/012620/AlphaDataCenter/NeuFactor/'
extend_factor_data_path = '/data/user/012620/AlphaDataCenter/Factor/longterm20/'
update_factor_help_path = '/data/user/012620/AlphaDataCenter/Transit/update_factor/'
extend_sample_path = depart_sample_path+'LFSample/feature/'
group_extend_path = depart_sample_path+'LFSample/group_extend_factors/'
num_threads = 10


factor_list_path = data_center_path+'Sample/factor_list.pkl'
hfactor_list_path = data_center_path+'HFSample/hfactor_list.pkl'
factor_info_path = depart_sample_path+'factor_info_nnnn.pkl'# factors in department sample 
factor_info_path_tmp = depart_sample_path+'factor_info_nnnn.pkl'
factor_custom_path = depart_sample_path+'factor_custom_dict.pkl'
factor_source_path = depart_sample_path+'factor_source_dict.pkl'
act_path = model_root_path+'DailyPrediction/'
model_path = model_root_path+'Models/'
weight_path = model_root_path+'DailyWeight/'
weight_hf_path = '/data/user/013546/alphahunter-strategy-python/input/Weight/'
prediction_path = model_root_path+'DailyPrediction/'
DepSample_path = depart_sample_path
TeamSample_path = data_center_path


name_map={'0930':'0930','1300':'pm','0930vwap':'vwap','0930vwap300':'vwap300','0930lf':'lf','0930hf':'hf'}
model_custom_params = {
        'vwap':{'KerasDeepFM':
                {'dfm_params':{'dropout_keep_fm': [0.2,0.2,0.2],'l1':0.001,
                    'l2': 0.1}
                }},
        'lf':{'KerasDeepFM':
                {'dfm_params':{'dropout_keep_fm': [0.2,0.2,0.2],'l1':0.001,
                    'l2': 0.1}
                 }}
         }

#['XgbSP_neu_vwap_re_5d','KerasDeepFMMulti_vwap_re_5d','LinearRegression_vwap_re_10d']   
#['XgbSP_neu_vwap_re_5d','KerasDeepFMMulti_vwap_re_5d','LinearRegression_vwap_NoExtremum_re_5d']        
model_config_dict = {
           '0930':[
               ('XgbSP','0930','neu_vwap_re_5d',5,240,True),
               ('LinearRegression','0930','0930_0959_re_5d',5,240,True),
               ('KerasDeepFMMulti','0930','0930_0959_re_5d',5,240,True)],
           'pm':[
               ('XgboostReg_Model_V1','pm','1300_1459_re_5d',5,240,True),
               ('LinearRegression','pm','1300_1459_re_5d',5,240,True),
               ('DeepFM','pm','1300_1459_re_5d',5,240,True)],
           'vwap':[
               ('XgbSP','vwap','neu_vwap_re_5d',5,240,True),                
               ('KerasDeepFMMulti','vwap','vwap_re_5d',5,480,False),
               ('LinearRegression','vwap','vwap_re_10d',10,240,True)               
               ],
           'vwap300':[
               ('XgbSP','vwap300','neu_vwap_re_5d',5,240,True),
               ('LinearRegression','vwap300','vwap_re_5d',5,240,True),
               ('KerasDeepFMMulti','vwap300','vwap_re_5d',5,480,False)],
           'lf':[
               ('LinearRegression','lf','vwap_NoExtremum_re_5d',5,240,True),
               ('XgbSP','lf','neu_vwap_re_5d',5,240,True),
               ('KerasDeepFMMulti','lf','vwap_re_5d',5,480,False),               
               ]
           }        
                              

model_name_map_500 = {k:[m[0]+'_'+m[2] for m in v] for k,v in model_config_dict.items()}
model_name_map_300 = {k:[m[0]+'_'+m[2] for m in v] for k,v in model_config_dict.items()}
model_name_map={'500':model_name_map_500,'300':model_name_map_300}

update_params={'5160503':\
{'label_open':True,'label_update':True,'mode_portfolio':1,\
'transaction_time':'0930vwap','captial_fake':60e7,'open_capital':60e7,\
'add_capital':1e8,'mode_open':1,'contact':'IC','benchmark':'500',\
'name':'QuantMachine500'},\
'5160803':\
{'label_open':True,'label_update':False,'mode_portfolio':1,\
'transaction_time':'0930','captial_fake':4e8,'open_capital':4e8,\
'add_capital':1e8,'mode_open':1,'contact':'IC','benchmark':'500',\
'name':'AlphaHunter500'},\
'5160304':\
{'label_open':True,'label_update':False,'mode_portfolio':1,\
'transaction_time':'0930vwap300','captial_fake':4e8,'open_capital':4e8,\
'add_capital':2e8,'mode_open':1,'contact':'IF','benchmark':'300',\
'name':'QuantMachine300'},\
'5161003':\
{'label_open':True,'label_update':False,'mode_portfolio':1,\
'transaction_time':'0930lf','captial_fake':6e8,'open_capital':6e8,\
'add_capital':1e8,'mode_open':1,'contact':'IC','benchmark':'500',\
'name':'Marathon'}}


