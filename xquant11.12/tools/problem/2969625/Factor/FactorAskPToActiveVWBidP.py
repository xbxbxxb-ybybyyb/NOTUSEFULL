# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/18
from System.Factor import Factor
import numpy as np


class FactorAskPToActiveVWBidP(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__fn = self._getParameter("ForwardN")

        self._addIntermediate("BidTradeAmount", [])
        self._addIntermediate("BidTradeVolume", [])
        self._addIntermediate("True", [])
        self._addIntermediate("Gap", [])
        self._addIntermediate("IsDefault", [])

    def calculate(self):
        bidm_list = self.getIntermediate("BidTradeAmount")
        bidv_list = self.getIntermediate("BidTradeVolume")
        true_list = self.getIntermediate("True")
        gap_list = self.getIntermediate("Gap")
        is_default_list = self.getIntermediate("IsDefault")

        # 最新逐笔成交价
        trade = self._getLastTickData("Transactions")
        if trade is not None:
            tradef = self._getTransactionData("BSFlag", trade)
            tradem = self._getTransactionData("Amount", trade)
            tradev = self._getTransactionData("Volume", trade)
            bidm_list.append(np.nansum(tradem[tradef == 1]))
            bidv_list.append(np.nansum(tradev[tradef == 1]))
        else:
            bidm_list.append(0.)
            bidv_list.append(0.)

        # 判断正确的距离
        if len(gap_list) >= self.__fn:
            askps = self._getLastNTickData("AskPrice", self.__fn + 1)
            bidps = self._getLastNTickData("BidPrice", self.__fn + 1)
            if (askps[0][0] > 0.01) and (bidps[-1][0] / askps[0][0] - 1 > 1e-6):
                true_list.append(gap_list[-self.__fn])
            else:
                true_list.append(np.nan)
        else:
            true_list.append(np.nan)

        # 是否使用默认距离
        is_default = is_default_list[-1] if len(is_default_list) > 0 else True

        # 因子值
        askp = self._getLastTickData("AskPrice")[0]
        if askp < 0.01:  # 涨停
            facv = self.getFactorValueList()[-self.__lag:]
            if len(facv) > 0:
                factorValue = np.nanmin(facv)
            else:
                factorValue = 0.
            gap = 0.002
        else:
            v = np.nansum(bidv_list[-self.__lag:])
            m = np.nansum(bidm_list[-self.__lag:])

            if v < 0.01:  # 长时间未成交
                last_facv = self.getLastFactorValue()
                if last_facv is not None:
                    factorValue = last_facv
                else:
                    factorValue = 0.
                gap = gap_list[-1] if len(gap_list) > 0 else 0.002
            else:
                if is_default:  # 非default后不再判断减少算量
                    if sum(~np.isnan(true_list)) > 20:
                        is_default = False

                if is_default:
                    bd = max([0.002, 0.02 / askp])
                else:
                    bd = np.nanpercentile(np.abs(true_list), 50)

                trade_vwap = m / v
                vwap_h = trade_vwap * (1 + bd)
                vwap_l = trade_vwap * (1 - bd)
                if vwap_l < askp < vwap_h:
                    nv = (askp / trade_vwap - 1) * 1e3
                elif askp >= vwap_h:
                    nv = ((vwap_h - (askp - vwap_h)) / trade_vwap - 1) * 1e3
                else:
                    nv = ((vwap_l - (askp - vwap_l)) / trade_vwap - 1) * 1e3

                facv = self.getFactorValueList()
                factorValue = self.__ema(nv, facv, self.__lag)

                gap = askp / trade_vwap - 1

        is_default_list.append(is_default)
        gap_list.append(gap)

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
