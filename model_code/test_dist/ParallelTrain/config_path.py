data_center_path = '/user/data/012620/AlphaDataCenter/'
basic_data_path = data_center_path+'Basic/'

transit_path = '/user/data/012620/AlphaDataCenter/Transit/'
hfactor_path = '/user/data/012620/AlphaDataCenter/HFactor/'

depart_sample_path = '/user/data/012620/AlphaDataCenter/Department/DepartSample/'

model_root_path = '/user/data/012620/AlphaDataCenter/Department/'
depart_factors_path = '/user/data/SHARE_2/alpha_factor/lib/x_factor_lib/'
minute_trade_price_path = '/user/data/012620/AlphaDataCenter/minute_trade_price/'

sample_norm_path = data_center_path+'Sample/NormSample/'

basic_daily_path = data_center_path+'Basic/daily/'
minute_data_path = data_center_path+'Basic/minute/'
factor_data_path = data_center_path+'Factor/daily/'
hfactor_data_path = data_center_path+'HFactor/one_pm/'
fund_factor_data_path = data_center_path+'Factor/fundamental_tmp/'
extend_sample_path = depart_sample_path+'LFSample/feature/'
group_extend_path = depart_sample_path+'LFSample/group_extend_factors/'


day_depart_feature_path = depart_sample_path+'Sample/feature/'
day_depart_label_path = depart_sample_path+'Sample/label/'
fix_depart_feature_path = depart_sample_path+'HFSample/feature/'
fix_depart_label_path = depart_sample_path+'HFSample/label/'


factor_list_path = data_center_path+'Sample/factor_list.pkl'
hfactor_list_path = data_center_path+'HFSample/hfactor_list.pkl'
factor_info_path = depart_sample_path+'factor_info_nnnn.pkl'
factor_info_path_tmp = depart_sample_path+'factor_info_nnnn.pkl'
factor_custom_path = '/user/data/012620/Share/factor_custom_dict_shp.pkl'
factor_source_path = depart_sample_path+'factor_source_dict.pkl'
act_path = model_root_path+'DailyPrediction/'
model_path = model_root_path+'Models/'
weight_path = model_root_path+'DailyWeight/'
prediction_path = model_root_path+'DailyPrediction/'
DepSample_path = depart_sample_path
TeamSample_path = data_center_path

factor_day_path_dict_test_path = '/user/data/012620/own/AlphaDataCenter/factor_day_path_dict_test.pkl'
factor_day_path_dict_test_rank_path = '/user/data/012620/own/AlphaDataCenter/factor_day_path_dict_test_rank.pkl'
factor_day_path_dict_test_zscore_path = '/user/data/012620/own/AlphaDataCenter/factor_day_path_dict_test_zscore.pkl'
factor_day_path_dict_test_rank_ind_path = '/user/data/012620/own/AlphaDataCenter/factor_day_path_dict_test_rank_ind.pkl'
factor_day_path_dict_test_zscore_ind_path = '/user/data/012620/own/AlphaDataCenter/factor_day_path_dict_test_zscore_ind.pkl'

factor_info_path_tmp = '/user/data/012620/AlphaDataCenter/Department/DepartSample/factor_info_nnnn.pkl'#@
factor_day_path_dict_path = '/user/data/012620/AlphaDataCenter/Department/DepartSample/factor_day_path_dict.pkl'#@
factor_fix_path_dict_path = '/user/data/012620/AlphaDataCenter/Department/DepartSample/factor_fix_path_dict.pkl'#@
factor_label_path_dict_path = '/user/data/012620/AlphaDataCenter/Department/DepartSample/factor_label_path_dict.pkl' #@
feature_fix_path = '/user/data/012620/AlphaDataCenter/Department/DepartSample/'
timepoint_list = ['0930','1000','1030','1100','1300','1330','1400','1430']

model_train_files_len_dict={'XgbSP':4,'KerasDeepFMMulti':20,'KerasDeepFMMulti_test':20,\
'KerasDeepFMMulti512_test':20,'LinearRegression':1,'GNN_chains':4}