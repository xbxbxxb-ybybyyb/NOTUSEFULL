from System.Factor import Factor
import numpy as np


class FactorPnlLinearPrediction(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")
        self.__tnum = self._getParameter("TicksPerMin")  # 个股每分钟有多少个Ticks
        self.__itnum = self._getParameter("ITicksPerMin")  # 指数每分钟有多少个Ticks
        self.__reglag = self._getParameter("RegressionLag")
        self.__ulag = self._getParameter("UpdateLag")
        self.__index_name = self._getParameter("IndexName")

        self.__hisReturnsList = None
        self.__hisReturnsIndexList = None
        self._addIntermediate("AlphaList", [])
        self._addIntermediate("BetaList", [])
        self._addIntermediate("ReturnsList", [])
        self._addIntermediate("ReturnsIndexList", [])

    def calculate(self):

        tsp = self._getAllTodayTickData("Timestamp")
        rtns = self.getIntermediate("ReturnsList")
        rtns_i = self.getIntermediate("ReturnsIndexList")
        alpha_list = self.getIntermediate("AlphaList")
        beta_list = self.getIntermediate("BetaList")
        lastp = self._getLastNTodayTickData("LastPrice", self.__mlag * self.__tnum + 1)
        lastp_i = self._getLastNTodayINFTickData(self.__index_name, "LastPrice", self.__mlag * self.__itnum + 1)

        if len(tsp) == 1:
            # 取出历史的收益率序列并算出第一个beta
            lastp_his = self._getAllHistoricalTickData("LastPrice")  # 前一天全部Tick
            lastp_i_his = self._getAllHistoricalINFTickData(self.__index_name, "LastPrice")
            tmp_rtns = (np.divide(lastp_his[self.__mlag * self.__tnum:], lastp_his[:-self.__mlag * self.__tnum]) - 1) * 100  # m分钟收益率
            tmp_rtns_i = (np.divide(lastp_i_his[self.__mlag * self.__itnum:], lastp_i_his[:-self.__mlag * self.__itnum]) - 1) * 100
            tmp_rtns = tmp_rtns[::-1][range(0, len(tmp_rtns), self.__tnum)][::-1]  # 1min采样一次
            tmp_rtns_i = tmp_rtns_i[::-1][range(0, len(tmp_rtns_i), self.__itnum)][::-1]

            ltrunc = np.nanmin([self.__reglag, len(tmp_rtns), len(tmp_rtns_i)])
            if ltrunc > 0:
                self.__hisReturnsList = list(tmp_rtns[-ltrunc:])
                self.__hisReturnsIndexList = list(tmp_rtns_i[-ltrunc:])
                alpha, beta = self.__get_regression_params(tmp_rtns_i[-ltrunc:], tmp_rtns[-ltrunc:])
            else:
                alpha, beta = np.nan, np.nan
            alpha_list.append(alpha)
            beta_list.append(beta)

        if len(tsp) >= self.__mlag * self.__tnum + 1:
            # 逐个加入当天最新的收益率
            rtns.append((lastp[-1] / lastp[0] - 1) * 100)
            rtns_i.append((lastp_i[-1] / lastp_i[0] - 1) * 100)
        else:
            rtns.append(None)
            rtns_i.append(None)

        # 一段时间更新一次beta
        if len(tsp) % self.__ulag == 0:
            valid_rtns = list(filter(lambda x: x is not None, rtns))
            valid_rtns_i = list(filter(lambda x: x is not None, rtns_i))
            rtns_all = self.__hisReturnsList + valid_rtns if self.__hisReturnsList is not None else valid_rtns
            rtns_i_all = self.__hisReturnsIndexList + valid_rtns_i if self.__hisReturnsIndexList is not None else valid_rtns_i
            alpha, beta = self.__get_regression_params(rtns_i_all[-self.__reglag:], rtns_all[-self.__reglag:])
            if not np.isnan(beta) and (beta != 0):  # 如果值正常才更新
                alpha_list.append(alpha)
                beta_list.append(beta)
            else:
                alpha_list.append(alpha_list[-1])
                beta_list.append(beta_list[-1])
        else:
            alpha_list.append(alpha_list[-1])
            beta_list.append(beta_list[-1])

        # 计算因子值
        if len(lastp_i) > 0:
            tmp_rtns = (lastp[-1] / lastp[0] - 1) * 100
            tmp_rtns_i = (lastp_i[-1] / lastp_i[0] - 1) * 100
            expected_rtns = alpha_list[-1] + beta_list[-1] * tmp_rtns_i
            if not np.isnan(expected_rtns):
                factorValue = expected_rtns - tmp_rtns
            else:  # 一般情况为前一天没有交易，第一个beta无法正常计算
                factorValue = 0
        else:
            factorValue = 0  # 前几个Tick可能正股数据取不出来

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_regression_params(x, y):
        x, y = np.array(x), np.array(y)
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) < 3 or len(x_) / len(x) < 0.5:
            alpha, beta = np.nan, np.nan
        else:
            beta = np.cov(y_, x_, bias=True)[0, 1] / np.var(x_)
            alpha = np.mean(y_) - beta * np.mean(x_)
        return alpha, beta
