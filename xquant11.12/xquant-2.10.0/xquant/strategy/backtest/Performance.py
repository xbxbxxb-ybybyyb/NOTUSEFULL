# _*_ coding:utf-8 _*_
import pandas as pd
import datetime as dt
from pandas import Series
import numpy as np
import math
from dateutil.relativedelta import relativedelta


class Performance(object):
    def __monthlyTerm_Startdate(self, end_date):
        '''
        根据传入的日期参数，计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date: 结束日期
        :return: 日期列表
        '''
        day = dt.datetime.strptime(str(end_date), "%Y%m%d")
        start_date_list = [
            (day + relativedelta(months=-1)).strftime("%Y%m%d"),
            (day + relativedelta(months=-3)).strftime("%Y%m%d"),
            (day + relativedelta(months=-6)).strftime("%Y%m%d"),
            (day + relativedelta(months=-12)).strftime("%Y%m%d")
        ]
        return start_date_list


    def __Strategic(self, data_Annualized):
        '''
        计算策略每日收益率
        :param data_Annualized: DataFrame
        :return: 策略每日收益率列表
        '''
        Pn = (data_Annualized - data_Annualized.shift(1)) / data_Annualized.shift(1)
        new_Pn = Pn.shift(-1)[:-1]
        return new_Pn

    def __benchmark(self, data_Benchmark):
        '''
        计算基准每日收益率
        :param data_Benchmark: DataFrame
        :param start_date: 开始时间
        :param end_date: 结束时间
        :return: 基准每日收益率列表
        '''
        Bn = (data_Benchmark - data_Benchmark.shift(1)) / data_Benchmark.shift(1)
        new_Bn = Bn.shift(-1)[:-1]
        return new_Bn

    def get_Strategic(self,data_Annualized,start_date, end_date):
        new_data_Annualized = data_Annualized.loc[int(start_date):int(end_date)]
        return self.__Strategic(new_data_Annualized)

    def get_benchmark(self,data_Benchmark, start_date, end_date):
        new_data_Benchmark = data_Benchmark.loc[int(start_date):int(end_date)]
        return self.__benchmark(new_data_Benchmark)

    def Annualized_Returns(self, data_Annualized, end_date, start_date=None):
        '''
        年化收益率(投资期限为一年的预期收益率)
        :param data_Annualized:DataFrame，历史总权益序列
        :param start_date:开始时间，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date:结束时间，int型，如：20170119
        :return:年化收益率列表，若start_date不为空则为单个元素的列表
        '''
        if not start_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        else:
            start_date_list = [start_date]
        pr_list = []
        for start_date in start_date_list:
            new_data_Annualized = data_Annualized.loc[int(start_date):int(end_date)]
            p_end = new_data_Annualized.iloc[-1]
            if math.isnan(p_end):
                return [np.nan]
            p_start = new_data_Annualized.iloc[0]
            n = len(new_data_Annualized)
            if n > 0:
                pr = (p_end / p_start) ** (250 / n) - 1
                pr_list.append(pr)
            else:
                pr_list.append(np.nan)
        return pr_list

    def Benchmark_Returns(self, data_Benchmark, end_date, start_date=None):
        '''
        基准年化收益率(表示参考标准年化收益率)
        :param data_Benchmark:DataFrame，历史指数收盘价序列
        :param start_date:开始时间，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date:结束时间，int型，如：20170119
        :return:基准年化收益率列表，若start_date不为空则为单个元素的列表
        '''
        if not start_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        else:
            start_date_list = [start_date]
        Bn_list = []
        for start_date in start_date_list:
            new_data_Benchmark = data_Benchmark.loc[int(start_date):int(end_date)]
            B_end = new_data_Benchmark.iloc[-1]
            if math.isnan(B_end):
                return [np.nan]
            B_start = new_data_Benchmark.iloc[0]
            n = len(new_data_Benchmark) - 1
            if n > 0:
                Bn = (B_end / B_start) ** (250 / n) - 1
                Bn_list.append(Bn)
            else:
                Bn_list.append(np.nan)
        return Bn_list

    def Beta(self, data_Annualized, data_Benchmark, end_date,start_date=None):
        '''
        贝塔(表示投资的系统性风险，反映了策略对大盘变化的敏感性)
        :param data_Annualized:DataFrame，历史总权益序列
        :param data_Benchmark:DataFrame，历史指数收盘价序列
        :param start_date:开始时间，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date:结束时间，int型，如：20170119
        :return:贝塔列表，若start_date不为空则为单个元素的列表
        '''
        if not start_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        else:
            start_date_list = [start_date]
        beta_list = []
        for start_date in start_date_list:
            new_data_Annualized = data_Annualized.loc[int(start_date):int(end_date)]
            new_data_Benchmark = data_Benchmark.loc[int(start_date):int(end_date)]
            Pn = self.__Strategic(new_data_Annualized).tolist()
            Bn = self.__benchmark(new_data_Benchmark).tolist()
            if len(Pn)>1 and len(Bn)>1:
                var_Bn = np.var(Bn)
                cov_ = np.cov(Pn, Bn)
                beta = cov_ / var_Bn
                beta_list.append(list(beta)[0][1])
            else:
                beta_list.append(np.nan)
        return beta_list

    def Alpha(self, data_Annualized, data_Benchmark, end_date, rf, start_date=None):
        '''
        阿尔法(投资者获得与市场波动无关的回报，一般用来度量投资者的投资技艺)
        :param data_Annualized:DataFrame，历史总权益序列
        :param data_Benchmark:DataFrame，历史指数收盘价序列
        :param start_date:开始时间，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date:结束时间，int型，如：20170119
        :param rf:无风险收益率
        :return:阿尔法列表，若start_date不为空则为单个元素的列表
        '''
        Pr_list = self.Annualized_Returns(data_Annualized, end_date, start_date)
        Br_list = self.Benchmark_Returns(data_Benchmark, end_date, start_date)
        beta_list = self.Beta(data_Annualized, data_Benchmark, end_date, start_date)
        alpha_list = []
        if not Pr_list:
            return [np.nan]
        for num in range(len(Pr_list)):
            try:
                alpha = Pr_list[num] - rf - beta_list[num] * (Br_list[num] - rf)
                alpha_list.append(alpha)
            except:
                alpha_list.append(np.nan)
        return alpha_list

    def Volatility(self, data_Annualized, end_date, start_date=None):
        '''
        收益波动率(用来测量资产的风险性，波动越大代表策略风险越高)
        :param data_Annualized:DataFrame，历史总权益序列
        :param start_date:开始时间，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date:结束时间，int型，如：20170119
        :return:收益波动率列表，若start_date不为空则为单个元素的列表
        '''
        if not start_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        else:
            start_date_list = [start_date]
        vol_list = []
        for start_date in start_date_list:
            new_data_Annualized = data_Annualized.loc[int(start_date):int(end_date)]
            Pt = self.__Strategic(new_data_Annualized)
            n = len(new_data_Annualized) - 1
            avg_Pt = np.mean(Pt)
            sum_Pt = 0
            for i in Pt:
                sum_Pt += (i - avg_Pt) ** 2
            if n == 1:
                vol_list.append(np.nan)
                continue
            v = 250 * sum_Pt / (n - 1)
            vol = math.sqrt(v)
            vol_list.append(vol)
        return vol_list

    def Sharpe_Ratio(self, data_Annualized, end_date, rf, start_date=None):
        '''
        夏普比率(表示每承受一单位总风险，会产生多少的超额报酬，可以同时对策略的收益与风险进行综合考虑)
        :param data_Annualized:DataFrame，历史总权益序列
        :param start_date:开始时间，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date:结束时间，int型，如：20170119
        :param rf:无风险收益率
        :return:夏普比率列表，若start_date不为空则为单个元素的列表
        '''
        Pr_list = self.Annualized_Returns(data_Annualized, end_date, start_date)
        vol_list = self.Volatility(data_Annualized, end_date, start_date)
        SR_list = []
        if not Pr_list:
            return [np.nan]
        for num in range(len(Pr_list)):
            if math.isnan(vol_list[num]) or not vol_list[num]:
                SR_list.append(np.nan)
            else:
                SR = (Pr_list[num] - rf) / vol_list[num]
                SR_list.append(SR)
        return SR_list

    def Information_Ratio(self,data_Annualized,data_Benchmark,end_date,start_date=None):
        """
        计算信息比率,衡量单位超额风险带来的超额收益
        :param data_Annualized: 历史总权益序列
        :param data_Benchmark: 历史指数收盘价序列
        :param end_date: 回测结束日期，int型，如：20170119
        :param satrt_date: 回测开始日期，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param return 信息比率列表，若start_date不为空则为单个元素的列表
        """
        start = data_Annualized.index[0]
        if not start_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        else:
            start_date_list = [start_date]
        InformationRatio_list = []
        for start_date in start_date_list:
            if int(start_date) < start:
                start_date = start
            Pr = self.Annualized_Returns(data_Annualized,end_date,start_date)
            Br = self.Benchmark_Returns(data_Benchmark,end_date,start_date)
            # 策略日收益率
            tactics_Profit_Ratio = self.get_Strategic(data_Annualized,start_date,end_date)
            # 基准日收益率
            benchmark_Profit_Ratio = self.get_benchmark(data_Benchmark,start_date,end_date)
            diff_Profit_Ratio = benchmark_Profit_Ratio - tactics_Profit_Ratio
            # 策略与基准每日收益率差值的标准差
            day_Profit_Ratio_std = Series.std(diff_Profit_Ratio)
            # 年化标准差
            year_Profit_Ratio_std = day_Profit_Ratio_std * pow(250,0.5)
            if not Pr or not Br or np.isnan(year_Profit_Ratio_std):
                InformationRatio_list.append(np.nan)
                continue
            else:
                InformationRatio = (Pr[0] - Br[0]) / year_Profit_Ratio_std
                InformationRatio_list.append(InformationRatio)
        return InformationRatio_list


    def Max_Drawdown(self,data_Annualized,end_date=None,start_date=None):
        """
        最大回撤
        :param data_Annualized: 历史总权益序列
        :param end_date: 结束日期，int型，如：20170119
        :param satrt_date: 开始日期，int型，如：20160109 ，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :return: 最大回撤列表，若start_date不为空则为单个元素的列表
        参数说明：
                  +------------+-----------+-----------------------+
                  | start_date | end_date |          return       |
                  +===============================================+
                  |    int    |    int    | 所传日期内的最大回撤  |
                  +-----------------------+-----------+-----------+
                  |    int    |    None   | 所传开始日期到回测    |
                  |           |           |结束日期内的最大回撤   |
                  +-----------------------+-----------+-----------+
                  |    None   |    int    | 过去一、三、六、      |
                  |           |           |十二个月的最大回撤     |
                  +-----------------------+-----------+-----------+
                  |    None   |    None   | 回测期间的最大回撤    |
                  +-----------------------+-----------+-----------+
        """
        # 回测时间的第一个交易日
        start = data_Annualized.index[0]
        # 回测时间的最后一个交易日
        end = data_Annualized.index[-1]
        equity_init = data_Annualized.copy()
        if not start_date and end_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        elif not start_date and not end_date:
            start_date_list = [start]
        else:
            start_date_list = [start_date]
        MaxDrawDown_list = []
        for start_ in start_date_list:
            if int(start_) < start:
                start_ = start
            if not end_date:
                end_date = end
            elif end_date > end:
                end_date = end
            if end_date:
                equity = equity_init.loc[start_:end_date]
            elif not end_date:
                equity = equity_init.loc[start_:]
            t = len(equity)
            drawDown = [0]
            for i in range(t - 1):
                Pi =equity.iloc[i]
                Pj = min(equity[i + 1:t])
                if Pi == 0.0:
                    continue
                draw_down = 1 - Pj / Pi
                drawDown.append(draw_down)
            MaxDrawDown = max(drawDown)
            MaxDrawDown_list.append(MaxDrawDown)
        return MaxDrawDown_list


    def Turnover_Rate(self,data_position,end_date,start_date=None):
        """
        计算年化换手率
        :param data_position: 持仓数量
        :param start_date: 回测开始日期,int型，如：20160109，为None时则计算过去一个月，过去三个月，过去六个月，过去十二个月的日期
        :param end_date: 回测结束日期，int型，如：20170119
        :return: 换手率列表，若start_date不为空则为单个元素的列表
        """
        # 回测开始时间的第一个交易日
        start = data_position.index.levels[0][0]
        if not start_date:
            start_date_list = self.__monthlyTerm_Startdate(end_date)
        else:
            start_date_list = [start_date]
        TurnoverRate_list = []
        data_position.sort_index(level=0,inplace=True)
        for start_date in start_date_list:
            if int(start_date) < start:
                start_date = start
            result = 0.0
            symbol_data = data_position.loc[int(start_date):int(end_date)].dropna()
            sort_key = list(symbol_data.index.levels[0]).index
            wdate = sorted(list(set(symbol_data.index.droplevel(1))),key=sort_key)
            N = len(wdate)
            if N > 1:
                for i in range(N-1):
                    position = 0.0
                    # j为股票代码
                    for j in symbol_data.loc[wdate[i]].index:
                        dt1 = wdate[i]
                        dt2 = wdate[i+1]
                        amount_1 = symbol_data.loc[dt1]
                        amount_2 = symbol_data.loc[dt2]
                        w1 = amount_1.loc[j] / amount_1.sum()
                        w2 = amount_2.loc[j] / amount_2.sum()
                        position += abs(w1 - w2)
                    result += position
                TurnoverRate = result * (250 / (N - 1))
                TurnoverRate_list.append(TurnoverRate)
            else:
                return [np.nan]
        return TurnoverRate_list





