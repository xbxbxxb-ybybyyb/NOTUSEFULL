# coding : utf-8
from tquant.strategy.factor_tester.test_data_loader import *
from dateutil.relativedelta import relativedelta
from tquant.strategy.factor_tester.factor_test_helper import *
from tquant import tq_logger


class FactorTestAnalysis:
    def __init__(self, factor_name, factor_value, excess_return_path, start_date='20160207', end_date='20181231',
                 price_type='vwap', rho=4e-4, top_range=0.1, neutralize=True, turnover_mode=True, ret_weight=False,
                 is_day_factor=True, vwap_13_type=0, local=True, in_sample_diff=1.0, out_sample_diff=0.6,
                 ret_threshold=0, corr_threshold=0.7, ret_oos=0):
        self.factor_name = factor_name
        self.factor_value = factor_value
        self.excess_return_path = excess_return_path
        self.start_date = start_date
        self.end_date = end_date

        self.price_type = price_type
        self.rho = rho
        self.neutralize = neutralize
        self.turnover_mode = turnover_mode
        self.top_range = top_range
        self.ret_weight = ret_weight
        self.factor_excess = None
        self.is_day_factor = is_day_factor
        self.vwap_13_type = vwap_13_type
        self.real_price_type = self.price_type
        if self.is_day_factor:
            self.real_price_type = self.price_type
        else:
            fix_time = self.factor_name[3:7]
            if fix_time[-2:] == '00':
                vwap_period = fix_time + '_' + fix_time[:2] + '30'
            else:
                vwap_period = fix_time + '_' + str(int(fix_time[:2]) + 1) + '00'

            if (fix_time == '1300') & (self.vwap_13_type == 1):
                vwap_period = '1300_1500'
            self.real_price_type = self.price_type + "_" + vwap_period
        self.local = local
        self.in_sample_diff = in_sample_diff
        self.out_sample_diff = out_sample_diff
        self.ret_threshold = ret_threshold
        self.corr_threshold = corr_threshold
        self.ret_oos = ret_oos
        if self.local:
            self.test_end_date = end_date
        else:
            self.test_end_date = dt.datetime.strptime(end_date, '%Y%m%d') - relativedelta(months=6)
            self.test_end_date = self.test_end_date.strftime("%Y%m%d")
        self.logger = tq_logger

    def launch_test(self):
        _ = self.get_n_max_corr()
        test_result, stat_result = self.get_final_flag(_)
        bool_flag = test_result.loc[self.factor_name, 'final_flag']
        # bie
        # save_excess_return(self.factor_name, self.factor_excess, self.real_price_type, self.local)
        # excess_return_path = os.path.join(self.excess_return_root, self.real_price_type)
        # if not os.path.exists(self.excess_return_path):
        #     raise Exception("the mount path not exists: '{0}'".format(self.excess_return_path))
        return {"factor": self.factor_name, "flag": bool_flag, "reason": test_result, "team": "analysis",
                "stat_result": stat_result}

    def get_n_max_corr(self, n=1):
        self.logger.debug("开始计算{0}与已上线因子的相关性及因子收益率！".format(self.factor_name))
        neu_factors_excess = self.get_neu_factor_excess_returns()

        save_factor_excess = self.get_excess_return(self.factor_value, self.start_date, self.end_date)

        if len(neu_factors_excess) < 1:
            return save_factor_excess, 1.0, None

        neu_factors_excess[self.factor_name] = save_factor_excess['excess_return']
        neu_factors_excess = pd.concat(neu_factors_excess, axis=1)
        neu_factors_excess.columns = neu_factors_excess.columns.levels[0]

        # get corr matrix
        factor_corr = neu_factors_excess.corr()
        factor_corr_df = factor_corr.abs().loc[self.factor_name]
        max_corr_score = factor_corr_df.sort_values(ascending=False).iloc[1:].head(n)

        return save_factor_excess, factor_corr_df, max_corr_score

    def get_neu_factor_excess_returns(self):
        neu_factors_excess = {}
        if not os.path.exists(self.excess_return_path):
            raise Exception("the mount path not exists: '{0}'".format(self.excess_return_path))

        file_list = os.listdir(self.excess_return_path)
        if file_list:
            for file in file_list:
                if not file.endswith('.pkl'):
                    continue
                neu_factor_name = file[:-4]
                if neu_factor_name == self.factor_name:
                    continue
                factor_excess_return_path = os.path.join(self.excess_return_path, file)
                neu_factor = pd.read_pickle(factor_excess_return_path)
                neu_factor = neu_factor.loc[self.start_date:self.test_end_date]
                neu_factor.columns = [neu_factor_name]
                neu_factors_excess[neu_factor_name] = neu_factor
            if len(neu_factors_excess) >= 1:
                self.logger.debug("已读取 {0} 个收益率文件".format(len(neu_factors_excess)))
        else:
            print("挂载路径为空，暂无上线因子的收益率文件！")
        return neu_factors_excess

    def get_excess_return(self, factor_df, start_date, end_date):
        # bie
        # price_adj = get_price_data(self.real_price_type)
        price_adj = get_price_data(self.real_price_type, start_date, end_date)
        self.logger.debug("计算{0}的复权因子price_adj:\n{1}".format(self.real_price_type, price_adj))

        if self.is_day_factor:
            if self.price_type == 'vwap':
                re_1d = price_adj.pct_change(1).shift(-2).iloc[:-2]
            elif self.price_type == 'close':
                re_1d = price_adj.pct_change(1).shift(-1).iloc[:-1]
            else:
                print('warning: price_type only is vwap or close.')
        else:
            re_1d = price_adj.pct_change(1).shift(-1).iloc[:-1]
        self.logger.debug("re_1d:\n{0}".format(re_1d))

        # assert start_date >= re_1d.index[0], 'start_date must be after than ' + re_1d.index[0]
        # assert end_date <= re_1d.index[-1], 'end_date must be before than ' + re_1d.index[-1]

        # bie
        self.logger.debug("读取alpha_universe.")
        is_valid = get_is_universe(start_date, end_date)
        self.logger.debug("计算is_valid_raw.")
        is_valid_raw = get_is_valid_raw(start_date, end_date)

        if self.is_day_factor:
            if self.price_type == 'vwap':
                is_valid = is_valid[np.logical_and(is_valid_raw.shift(-2) == 1, is_valid_raw.shift(-1) == 1)]
            elif self.price_type == 'close':
                is_valid = is_valid[is_valid_raw.shift(-1) == 1]
        else:
            is_valid = is_valid[is_valid_raw.shift(-1) == 1]

        is_valid01 = (is_valid == 1).loc[start_date:end_date]
        re_1d = re_1d[is_valid01].loc[start_date:end_date]

        excess_return = re_1d.subtract(re_1d.mean(axis=1), axis=0)
        factor_df = factor_df[is_valid01]
        factor_df.dropna(how='all', axis=0, inplace=True)

        if self.neutralize:
            self.logger.debug("对检测因子的数据进行行业中性化处理！")
            factor_df = self.get_neu_factor(factor_df)

        # update_date_list_end = factor_df.index[-2]
        factor_ranker_pct_descending = factor_df.rank(pct=True, axis=1, method='first', ascending=False)

        turnover_rate = 0
        wi_descending_01 = ((factor_ranker_pct_descending <= self.top_range) * 1).fillna(0)
        wi_descending = factor_ranker_pct_descending.fillna(0) * wi_descending_01

        # weighted
        if self.ret_weight:
            wi_descending = wi_descending.applymap(self.weight_descending_mapping)
            wi_descending = wi_descending.astype(float)
        else:
            wi_descending = wi_descending_01

        if self.turnover_mode:
            wi_turnover = (wi_descending - wi_descending.shift(1)).applymap(abs) / 2
            turnover_rate = wi_turnover.sum(axis=1) / wi_descending.sum(axis=1)
            turnover_rate[np.isinf(turnover_rate)] = np.nan

        wi_descending = wi_descending.divide(wi_descending.sum(axis=1), axis=0)
        self.logger.debug("wi_descending:\n{0}".format(wi_descending))

        ########################
        excess_descending = ((wi_descending * excess_return).sum(axis=1))#[start_date:update_date_list_end]
        excess_descending = excess_descending - self.rho * turnover_rate

        save_factor_excess = excess_descending.to_frame()
        save_factor_excess.columns = ['excess_return']
        self.factor_excess = save_factor_excess[start_date:end_date]
        self.logger.debug("因子{0}的收益率：\n{1}".format(self.factor_name, self.factor_excess))

        return save_factor_excess.loc[start_date:end_date]

    @staticmethod
    def get_neu_factor(factor_df):
        factor_start_date = factor_df.index[0]
        factor_end_date = factor_df.index[-1]

        industry_code_all = get_industry_code_all(factor_start_date, factor_end_date)
        industry_list = industry_code_all.stack().unique()
        industry_list = industry_list[industry_list != 0]

        industry_mark = {}
        for industry in industry_list:
            tmp = pd.DataFrame(0., index=industry_code_all.index, columns=industry_code_all.columns)
            tmp[industry_code_all == industry] = 1
            industry_mark[industry] = tmp
        industry_mark_df = pd.concat(industry_mark)

        size = get_mkt_cap_ard(factor_start_date, factor_end_date)
        size = np.log(size)

        norm_size = Normalization2(size, axis=0)
        norm_size = norm_size.norm_dataframe()

        if industry_code_all.index[-1] != norm_size.index[-1]:
            assert False
        if industry_code_all.index[0] != norm_size.index[0]:
            assert False
        try:
            dates_need_update = factor_df.index.tolist()
            factor_neu_update = update_neu_factor(factor_df, norm_size, industry_mark_df, dates_need_update)
            factor_neu_all = factor_neu_update
            factor_neu_all = factor_neu_all.sort_index()
            return factor_neu_all
        except:
            raise AssertionError("factor data has some problem in neutralization, please check your data.")

    def get_final_flag(self, details):
        save_factor_excess, _, max_corr_score = details
        start_date, end_date = save_factor_excess.index[0], save_factor_excess.index[-1]
        flag_total = pd.DataFrame(index=[self.factor_name], columns=['ret_flag', 'corr_flag', 'sample_flag'])
        stat_value_dict = {}

        in_sample_excess = save_factor_excess.loc[start_date:self.test_end_date, 'excess_return']
        out_sample_excess = save_factor_excess.loc[self.test_end_date:end_date, 'excess_return']

        ret_value = in_sample_excess.mean()
        # 样本内（2016.1.1—2018.12.31）的头部组合（Top10%）超额收益大于0
        flag_total.loc[self.factor_name, 'ret_flag'] = ret_value > self.ret_threshold
        stat_value_dict['ret_result'] = ret_value

        # 新入库的因子必须与已入库的所有因子的相关性都小于0.7
        if max_corr_score is None:
            flag_total.loc[self.factor_name, 'corr_flag'] = True
            stat_value_dict['corr_result'] = 0
        else:
            corr_value = max_corr_score.values[0]
            flag_total.loc[self.factor_name, 'corr_flag'] = corr_value < self.corr_threshold
            stat_value_dict['corr_result'] = corr_value

        self.logger.debug("与已上线因子的相关性为 {0}".format(stat_value_dict['corr_result']))
        # 样本内对超额收益抽样10次,计算统计量D，要求D < 1.0
        flag_total.loc[self.factor_name, 'sample_flag'], ret_diff_value = self.get_sample_flag(in_sample_excess)
        stat_value_dict['sample_result'] = ret_diff_value

        if self.local:
            flag_total.loc[self.factor_name, 'final_flag'] = flag_total.iloc[0].all()
        else:
            # 样本外（2019.1.1—2019.6.30）的头部组合超额收益大于0
            oos_ret_value = out_sample_excess.mean()
            flag_total.loc[self.factor_name, 'oos_ret_flag'] = oos_ret_value > self.ret_oos
            flag_total.loc[self.factor_name, 'final_flag'] = flag_total.iloc[0].all()
            stat_value_dict['oos_ret_result'] = oos_ret_value
        stat_value_dict['statu'] = self.calc_statu(flag_total)
        self.logger.debug("flag_total:\n{0}".format(flag_total))
        self.logger.debug("stat_value_dict:\n{0}".format(stat_value_dict))

        return flag_total, stat_value_dict

    def calc_statu(self, df):
        sta_map = {'ret_flag': 4, 'corr_flag': 5, 'sample_flag': 6}
        res_dic = df.loc[self.factor_name].to_dict()
        if res_dic['final_flag']:
            statu = 2
        else:
            res_dic.pop('final_flag')
            for k in res_dic:
                if not res_dic[k]:
                    res_dic[k] = sta_map[k]
                else:
                    res_dic[k] = 0
            statu = res_dic['ret_flag'] + res_dic['corr_flag'] + res_dic['sample_flag']
        return statu

    def get_sample_flag(self, excess, in_sample=True, random_state=0, bootstrap_steps=9, experiment_steps=10):
        assert bootstrap_steps >= 1, "bootstrap_steps must be >= 1"
        ret_diff = []  # record sample excess of each sample process

        for i in range(experiment_steps):
            ret_diff.append(
                self.sample_random(excess, random_state=random_state, bootstrap_steps=bootstrap_steps) * 1e4)
            random_state += 1
        ret_diff = pd.Series(ret_diff)
        ret_diff_mean = abs(ret_diff.mean())

        if ret_diff_mean == 0:
            return False
        ret_diff_gap = ret_diff.nlargest(experiment_steps // 2).mean() - ret_diff.nsmallest(
            experiment_steps // 2).mean()
        ret_diff_value = ret_diff_gap / ret_diff_mean

        # global sample_diff_standard
        if in_sample:
            # bie
            return ret_diff_value < self.in_sample_diff, ret_diff_value
        else:
            return ret_diff_value < self.out_sample_diff, ret_diff_value

    @staticmethod
    def weight_descending_mapping(x):
        if x <= 0:
            return 0
        elif x <= 0.05:
            return 4.
        elif x <= 0.10:
            return 3.
        elif x <= 0.15:
            return 2.
        elif x <= 0.20:
            return 1.

    @staticmethod
    def sample_random(excess, random_state, bootstrap_steps):
        from sklearn.model_selection import train_test_split
        # sample containing two parts
        # part 1: 10% of the sample
        sample_10, sample_90 = train_test_split(excess, test_size=1 - 1 / (bootstrap_steps + 1),
                                                random_state=random_state)
        # part 2:bootstrap sampling of the rest 90%
        excess_sample = sample_10.tolist()
        for i in range(bootstrap_steps):
            sample_new = sample_90.sample(n=len(sample_10), replace=True, random_state=random_state).tolist()
            excess_sample += sample_new
            random_state += 10
        return pd.Series(excess_sample).mean()

    def save_execss(self, path):
        temp_save_daily_excess_return(self.factor_name,
                                      self.get_excess_return(self.factor_value, self.start_date, self.end_date), path)
