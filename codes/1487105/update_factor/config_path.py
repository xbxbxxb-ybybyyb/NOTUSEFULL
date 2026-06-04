data_center_path = '/data/user/012620/AlphaDataCenter/'
factor_save_path = data_center_path
update_factor_help_path = data_center_path+'Transit/update_factor/'
update_date_path = update_factor_help_path+'start_end_date.pkl'
factor_dict_ori = update_factor_help_path+'factor_dict.pkl'
aimr_factor_dict_path = update_factor_help_path+'aimr_add_multi_factor_dict.pkl'
multi_factor_dict_path = update_factor_help_path+'multi_factor_dict.pkl'
basic_data_path = data_center_path+'Basic/'
basic_minute_path = basic_data_path+'minute/'
basic_daily_path = basic_data_path+'daily/'
factor_help_path = factor_save_path+'Transit/factor_intermediate/'
factor_data_path = factor_save_path+'Factor/'

code_root_path ='/data/user/012620/shipan2/AlphaFramework/'
alpha_tool_path = code_root_path+'AnalysisTool/'
factor_management_path = code_root_path+'FactorManagement/'
update_factor_code_path = code_root_path+'DataPreprocessor/'

index_factors = ['MinIdx300Corr','MinIdx500Corr']
import datetime
today = datetime.date.today().strftime('%Y%m%d')
#today = '20211029'