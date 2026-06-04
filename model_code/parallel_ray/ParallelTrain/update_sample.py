from DataAPI.DataToolkit import *
from ModelSystem.Tools import *


def load_sample(factor_list, model_retrain_date, strategy_type, label_name, gap):
    root_path = os.path.dirname(os.path.abspath(__file__))
    root_path = "/data/user/013150/ai_data"
    file_path = os.path.join(root_path, "factordata_{}_{}_{}_{}.pkl".format(model_retrain_date[-1], strategy_type, label_name, gap))
    if os.path.exists(file_path):
        return pd.read_pickle(file_path)
    factor_intra = [x for x in factor_list if re.match(r"^Fix\d+_.*", x)]
    factor_vwap = list(set(factor_list) - set(factor_intra))
    factor_vwap3 = []
    sample = []
    label_address = '/data/user/666889/Apollo/Sample/Label'
    factor_vwap_address = '/data/user/666889/Apollo/Sample/Feature/vwap'
    factor_intra_address = '/data/user/666889/Apollo/Sample/Feature'
    label_name_load = '{}_{}d'.format(label_name, gap)

    for date in model_retrain_date:
        # print('Loading sample {}'.format(date))
        sample_day = None
        feature_intra_day = date
        feature_vwap_day = Dtk.get_n_days_off(date, -2)[0]

        if factor_vwap.__len__() > 0:
            df = pd.read_pickle('{}/{}.pkl'.format(factor_vwap_address, feature_vwap_day))
            factor_columns = list(df.columns)
            factor_vwap2 = [x for x in factor_vwap if x in factor_columns] + [x+'_team' for x in factor_vwap if x not in factor_columns]
            factor_vwap3 = [x for x in factor_vwap if x in factor_columns] + [x for x in factor_vwap if x not in factor_columns]
            sample_day = df[['stock'] + factor_vwap2]
            sample_day.columns = ['stock'] + factor_vwap3
        if factor_intra.__len__() > 0:
            df = pd.read_pickle('{}/{}/{}.pkl'.format(factor_intra_address, strategy_type, feature_intra_day))
            if sample_day is None:
                sample_day = df[['stock'] + factor_intra]
            else:
                sample_day = sample_day.merge(df[['stock'] + factor_intra], on=['stock'], how='left')

        df = pd.read_pickle('{}/{}/{}.pkl'.format(label_address, strategy_type, date))[['date', 'stock', label_name_load]]
        df.rename(columns={label_name_load: label_name}, inplace=True)
        sample_day = df.merge(sample_day[['stock'] + factor_vwap3+factor_intra], how='left', on=['stock'])
        sample_day.dropna(inplace=True)
        sample.append(sample_day)
    sample = pd.concat(sample)

    df = sample.reset_index(drop=True)
    df.to_pickle(file_path)
    print("get_data factordata_{}_{}_{}_{}.pkl".format(model_retrain_date[-1], strategy_type, label_name, gap) )
    return df


def load_sample_con(factor_list, model_retrain_date, label_name, gap, train_sample_times):
    raise Exception()
    sample = []
    label_address = '/data/user/666889/Apollo/Sample/Label'
    factor_vwap_address = '/data/user/666889/Apollo/Sample/Feature/vwap'
    factor_intra_address = '/data/user/666889/Apollo/Sample/Feature'
    label_name_load = '{}_{}d'.format(label_name, gap)

    for date in model_retrain_date:
        print('Loading sample {}'.format(date))
        df_vwap = None
        feature_intra_day = date
        feature_vwap_day = Dtk.get_n_days_off(date, -2)[0]

        factor_vwap = factor_list['daily']
        factor_vwap3 = []
        if factor_vwap.__len__() > 0:
            df_vwap = pd.read_pickle('{}/{}.pkl'.format(factor_vwap_address, feature_vwap_day))
            factor_columns = list(df_vwap.columns)
            factor_vwap2 = [x for x in factor_vwap if x in factor_columns] + [x + '_team' for x in factor_vwap if
                                                                              x not in factor_columns]
            factor_vwap3 = [x for x in factor_vwap if x in factor_columns] + [x for x in factor_vwap if
                                                                              x not in factor_columns]
            df_vwap = df_vwap[['stock'] + factor_vwap2]
            df_vwap.columns = ['stock'] + factor_vwap3

        for sample_time in train_sample_times:
            sample_day = df_vwap
            factor_intra = ['Fix_{}'.format(x) for x in factor_list['intra']]

            if factor_intra.__len__() > 0:
                df = pd.read_pickle('{}/{}/{}.pkl'.format(factor_intra_address, sample_time, feature_intra_day))
                columns_all = ['date', 'stock']+['Fix_{}'.format(x[8:]) for x in list(df.columns) if re.match(r"^Fix\d+_.*", x)]
                df.columns = columns_all
                if sample_day is None:
                    sample_day = df[['stock'] + factor_intra]
                else:
                    sample_day = sample_day.merge(df[['stock'] + factor_intra], on=['stock'], how='left')

            df = pd.read_pickle('{}/{}/{}.pkl'.format(label_address, sample_time, date))[['date', 'stock', label_name_load]]
            df.rename(columns={label_name_load: label_name}, inplace=True)
            sample_day = df.merge(sample_day[['stock'] + factor_vwap3+factor_intra], how='left', on=['stock'])
            sample_day.dropna(inplace=True)
            sample.append(sample_day)
    sample = pd.concat(sample)

    return sample.reset_index(drop=True)


def load_sample2(factor_list, sample_dates, strategy_type='lf', label_name='vwap_re_5d', gap=5):
    raise Exception()
    complete_stock_list = get_complete_stock_list()
    start_date = sample_dates[0]
    end_date = sample_dates[-1]
    label_df = load_label(sample_dates[0], sample_dates[-1], complete_stock_list, label_type=label_name, holding_period=gap, time_interval=strategy_type)

    if strategy_type in ['0930', '1000', '1030', '1100', '1300', '1330', '1400', '1430']:
        sample = load_intra_all_factor_suanfa(start_date, end_date, strategy_type, complete_stock_list, factor_list)
    else:
        sample = load_day_factor(start_date, end_date, complete_stock_list, factor_list)

    label_df.index = sample[list(sample.keys())[0]].index

    sample.update({label_name: label_df})

    temp_code = list(label_df.columns)
    temp_timestamp = list(label_df.index)
    temp_code = np.repeat(temp_code, label_df.shape[0])
    temp_timestamp = np.tile(temp_timestamp, label_df.shape[1])
    temp_data = np.array([sample[i].values for i in factor_list+[label_name]]).transpose([2, 1, 0]).reshape([temp_code.__len__(), factor_list.__len__()+1])
    sample = pd.DataFrame(temp_data, columns=factor_list+[label_name])
    sample['stock'] = temp_code
    sample['timestamp'] = temp_timestamp

    return sample.dropna()



