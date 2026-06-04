import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from DataAPI.AddressManagement import AddressManagement
from DataAPI.FactorTestloader import *
from Utils.HelperFunctions import *
import pickle
from multiprocessing import Pool
from sklearn.feature_selection import SelectFromModel
from sklearn.svm import LinearSVC
from sklearn.ensemble import ExtraTreesClassifier

addressManagement = AddressManagement()
root = addressManagement.get_root()
root_666889 = addressManagement.get_root('666889')

start_date = 20140514
end_date = 20190730
pred_period = 5
train_lag = 120
trading_date_list = Dtk.get_trading_day(start_date, end_date)
start_date_lag = Dtk.get_n_days_off(trading_date_list[0], -pred_period - train_lag - 2)[0]
start_date_datetime = Dtk.convert_date_or_time_int_to_datetime(start_date_lag)
end_date_datetime = Dtk.convert_date_or_time_int_to_datetime(end_date)
factor_file_name = "factors_benchmark"
label_type = "max_daily_twap"
total_factor_list = list(pd.read_excel(root + "/Apollo/FactorSelecting/" + factor_file_name + ".xlsx", header=None).values.flatten())
feature_select_path = root + "/Apollo/FactorSelecting/select_from_model_lsvc0.005_factors_benchmark_tag_maxdaily5"
if not os.path.exists(feature_select_path):
    os.mkdir(feature_select_path)
neutral_factor_path = root_666889 + "/Apollo/AlphaFactors/AlphaFactorsStandardized/"


def feature_select_corr(X: pd.DataFrame, y: pd.Series, corr_threshold):
    std_X = X.std(axis=0)
    columns_delete = std_X[std_X < 0.8].index
    X.drop(columns_delete, axis=1, inplace=True)
    corr_y = X.corrwith(y).abs()
    corr_df = X.corr()
    factor_list = X.columns.tolist()
    keep_factors = []
    drop_factors = []
    for factor_name in factor_list:
        factor_set = list(set(factor_list) - set(drop_factors) - set([factor_name]))
        corr_factor = corr_df.loc[factor_name, factor_set]
        if (abs(corr_factor)).max() < corr_threshold:
            keep_factors.append(factor_name)
        else:
            similar_factors = corr_factor[corr_factor.abs() >= corr_threshold].index.tolist()
            if corr_y.loc[factor_name] > corr_y.loc[similar_factors].max():
                keep_factors.append(factor_name)
            else:
                drop_factors.append(factor_name)
    return keep_factors


def feature_select_from_model(X: pd.DataFrame, y: pd.Series):
    lsvc = LinearSVC(C=0.005, penalty='l1', dual=False).fit(X, y)
    feature_select = SelectFromModel(lsvc, prefit=True)
    # clf = ExtraTreesClassifier(n_estimators=100)
    # clf = clf.fit(X, y)
    # feature_select = SelectFromModel(clf, prefit=True)
    return feature_select


def change_to_classif(original_label_data_df, alpha_universe, percent_select):
    label_df = original_label_data_df.copy()
    label_df[:] = np.nan
    for i in range(alpha_universe.__len__() - 1):
        stock_list = alpha_universe.iloc[i, :]
        # daily_industry = self.industry_info.iloc[i, :]
        temp_label_data = original_label_data_df.iloc[i + 1, :].dropna()
        temp_label_data = temp_label_data[stock_list == 1].sort_values()
        n_stock_select = np.multiply(percent_select, temp_label_data.shape[0])
        n_stock_select = np.around(n_stock_select).astype(int)
        temp_label_data.iloc[:] = np.nan
        temp_label_data.iloc[0:n_stock_select[0]] = 0
        temp_label_data.iloc[-n_stock_select[1]:] = 1
        label_df.iloc[i + 1, :] = temp_label_data
    label_df = label_df.shift(-1)  # 将标签与因子的时间轴对齐
    return label_df


complete_stock_list = Dtk.get_complete_stock_list()
alpha_universe = Dtk.get_panel_daily_info(complete_stock_list, start_date_lag, end_date, 'alpha_universe')
percent_select = [0.3, 0.3]
total_factor_data = {}
for factor in total_factor_list:
    temp_factor = load_factor(factor, complete_stock_list, start_date_datetime, end_date_datetime, neutral_factor_path)
    total_factor_data.update({factor: temp_factor})
    print(factor + " has been loaded")

label_data = load_label(complete_stock_list, start_date_lag, end_date, label_type, pred_period,
                        output_index_type='timestamp', forward_shift=True)
label_data = change_to_classif(label_data, alpha_universe, percent_select)


def calculate(date):
    t1 = dt.datetime.now()
    train_date_day_factor_end = Dtk.get_n_days_off(date, -pred_period - 3)[0]
    train_date_day_factor_start = Dtk.get_n_days_off(date, -pred_period - train_lag - 2)[0]

    start = str(train_date_day_factor_start) + ' 00:00:00'
    end = str(train_date_day_factor_end) + ' 23:59:59'
    date_start = dt.datetime.strptime(start, '%Y%m%d %H:%M:%S').timestamp()
    date_end = dt.datetime.strptime(end, '%Y%m%d %H:%M:%S').timestamp()

    # 将因子值和标签按照时间+股票重新排列，每一列对应因子或者标签，每一行为一个样本，剔除非正例或反例以及因子值缺失的样本
    day_factor_df = pd.DataFrame()
    for factor in total_factor_list:
        day_factor_df[factor] = total_factor_data[factor].loc[date_start:date_end, :].stack(dropna=False)
    day_factor_df['label'] = label_data.loc[date_start:date_end, :].stack(dropna=False)
    day_factor_df.dropna(subset=['label'], axis=0, inplace=True)
    day_factor_df.fillna(0, inplace=True)

    # 设置模型
    factor_df = day_factor_df.loc[:, total_factor_list]
    label_sr = day_factor_df.loc[:, 'label']
    # feature_select = feature_select_from_model(factor_df, label_sr)
    # with open(feature_select_path + "/feature_select_" + str(date) + ".pickle", "wb") as f:
    #     pickle.dump(feature_select, f)
    selected_factors = feature_select_corr(factor_df, label_sr, 0.8)
    print(selected_factors)
    print(len(selected_factors))
    if not os.path.exists(root + '/Apollo/FactorSelecting/' + factor_file_name):
        os.mkdir(root + '/Apollo/FactorSelecting/' + factor_file_name)
    with open(root + '/Apollo/FactorSelecting/' + factor_file_name + '/factors_selected_' + str(date) + '.pickle', 'wb') as f:
        pickle.dump(selected_factors, f)
    t2 = dt.datetime.now()
    print(t2 - t1)


pool = Pool(10)
for i, trading_date in enumerate(trading_date_list):
    if i % 10 != 0:
        continue
    print(trading_date)
    pool.apply_async(calculate, args=(trading_date,))
pool.close()
pool.join()
