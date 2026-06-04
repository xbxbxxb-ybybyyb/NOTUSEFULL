from System.Factor import Factor
import numpy as np


class FactorCBRelativeReturnsUA(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__rmlag = self._getParameter("ReturnsMinLag")
        self.__reglag = self._getParameter("RegressionLag")
        self.__ulag = self._getParameter("UpdateLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__midPriceHis = self._getFactor(
            {
                "ClassName": "MidPriceHistorical",
                "TickLength": 1
            }
        )
        self.__hisReturnsList = None
        self.__hisReturnsUAList = None
        self._addIntermediate("AlphaList", [])
        self._addIntermediate("BetaList", [])
        self._addIntermediate("ReturnsList", [])
        self._addIntermediate("ReturnsUAList", [])

    def calculate(self):

        tsp = self._getAllTodayTickData("Timestamp")
        alpha_list = self.getIntermediate("AlphaList")
        beta_list = self.getIntermediate("BetaList")
        rtns = self.getIntermediate("ReturnsList")
        rtns_ua = self.getIntermediate("ReturnsUAList")
        midp = self.__midPrice.getFactorValueList()[-self.__rmlag * 20:]
        lastp_ua = self._getLastNTodayTickDataUA("LastPrice", self.__rmlag * 20)

        if len(tsp) == 1:
            # 取出历史的收益率序列并算出第一个beta
            midp_his = self.__midPriceHis.getFactorValueList()[0]
            lastp_ua_his = self._getAllHistoricalTickDataUA("LastPrice")
            tmp_rtns = (np.divide(midp_his[self.__rmlag * 20:], midp_his[:-self.__rmlag * 20]) - 1) * 100
            tmp_rtns_ua = (np.divide(lastp_ua_his[self.__rmlag * 20:], lastp_ua_his[:-self.__rmlag * 20]) - 1) * 100
            ltrunc = np.nanmin([self.__reglag, len(tmp_rtns), len(tmp_rtns_ua)])
            if ltrunc > 0:
                self.__hisReturnsList = tmp_rtns[-ltrunc:].tolist()
                self.__hisReturnsUAList = tmp_rtns_ua[-ltrunc:].tolist()
                alpha, beta = self.get_regression_params(tmp_rtns_ua[-ltrunc:], tmp_rtns[-ltrunc:])
            else:
                alpha, beta = np.nan, np.nan
            alpha_list.append(alpha)
            beta_list.append(beta)

        if len(tsp) >= self.__rmlag * 20:
            # 逐个加入当天最新的收益率
            rtns.append((midp[-1] / midp[0] - 1) * 100)
            rtns_ua.append((lastp_ua[-1] / lastp_ua[0] - 1) * 100)
        else:
            rtns.append(None)
            rtns_ua.append(None)

        # 一段时间更新一次beta
        if len(tsp) % self.__ulag == 0:
            valid_rtns = list(filter(lambda x: x is not None, rtns))
            valid_rtns_ua = list(filter(lambda x: x is not None, rtns_ua))
            rtns_all = self.__hisReturnsList + valid_rtns if self.__hisReturnsList is not None else valid_rtns
            rtns_ua_all = self.__hisReturnsUAList + valid_rtns_ua if self.__hisReturnsUAList is not None else valid_rtns_ua
            alpha, beta = self.get_regression_params(rtns_ua_all[-self.__reglag:], rtns_all[-self.__reglag:])
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
        if len(lastp_ua) > 0:
            tmp_rtns = (midp[-1] / midp[0] - 1) * 100
            tmp_rtns_ua = (lastp_ua[-1] / lastp_ua[0] - 1) * 100
            expected_rtns = alpha_list[-1] + beta_list[-1] * tmp_rtns_ua
            if not np.isnan(expected_rtns):
                factorValue = expected_rtns - tmp_rtns
            else:  # 一般情况为前一天没有交易，第一个beta无法正常计算
                factorValue = 0
        else:
            factorValue = 0  # 前几个Tick可能正股数据取不出来

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def get_regression_params(x, y):
        x, y = np.array(x), np.array(y)
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) < 3 or len(x_) / len(x) < 0.5:
            return np.nan, np.nan
        beta = np.cov(y_, x_, bias=True)[0, 1] / np.var(x_)
        alpha = np.mean(y_) - beta * np.mean(x_)
        return alpha, beta
