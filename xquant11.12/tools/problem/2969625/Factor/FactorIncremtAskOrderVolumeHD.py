from System.Factor import Factor
import numpy as np


class FactorIncremtAskOrderVolumeHD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__n = self._getParameter("NumGroups")

        self.__historicalDensity = None
        self.__historicalCutoff = None

        self._addIntermediate("AlternativeDensity", [])
        self._addIntermediate("AlternativeCutoff", [])

        self._addIntermediate("IncremtAskOrderVolumeList", [])
        self._addIntermediate("LastAskPriceList", [])
        self._addIntermediate("LastAskVolumeList", [])

    def calculate(self):

        incremt_askv_list = self.getIntermediate("IncremtAskOrderVolumeList")
        last_askp_list = self.getIntermediate("LastAskPriceList")
        last_askv_list = self.getIntermediate("LastAskVolumeList")
        alternative_density = self.getIntermediate("AlternativeDensity")
        alternative_cutoff = self.getIntermediate("AlternativeCutoff")

        if alternative_density:
            alternative_density.append(alternative_density[-1])
            alternative_cutoff.append(alternative_cutoff[-1])
        else:
            alternative_density.append(None)
            alternative_cutoff.append(None)

        last_askp = last_askp_list[-1] if last_askp_list else None
        last_askv = last_askv_list[-1] if last_askv_list else None
        askp = self._getLastTickData("AskPrice")
        askv = self._getLastTickData("AskVolume")
        trans = self._getLastTickData("Transactions")

        if last_askp is not None and askp is not None:
            incremt_askv = self.__incremental_ask_volume(last_askp, last_askv, askp, askv)

            if trans is not None:
                bsflag = self._getTransactionData("BSFlag", trans)
                volume = self._getTransactionData("Volume", trans)
                incremt_askv += np.nansum(volume[bsflag == 2])

            incremt_askv_list.append(incremt_askv)

            # 历史信息缺失，使用当天前600个Tick信息代替历史分布，后续不变化
            if self.__historicalDensity is None and (len(incremt_askv_list) > 600) and (alternative_density[-1] is None):
                minv = np.percentile(incremt_askv_list, 10)
                maxv = np.percentile(incremt_askv_list, 90)
                vcutoff = np.append(np.insert(np.linspace(minv, maxv, self.__n + 1), 0, -np.inf), np.inf)
                density = self.__get_density(incremt_askv_list, vcutoff)
                alternative_cutoff[-1] = vcutoff
                alternative_density[-1] = density

            # 计算因子
            historical_density = self.__historicalDensity if self.__historicalDensity is not None else alternative_density[-1]
            historical_cutoff = self.__historicalCutoff if self.__historicalCutoff is not None else alternative_cutoff[-1]

            if historical_density is not None:
                sub_askv_list = np.array(incremt_askv_list[-self.__lag:])
                density = self.__get_density(sub_askv_list, historical_cutoff)

                factorValue = np.sqrt(1-np.nansum(np.sqrt(historical_density*density)))
                if np.nanmean(sub_askv_list) < np.nanmedian(historical_cutoff):
                    factorValue = -factorValue
            else:
                factorValue = 0.

        else:
            incremt_askv_list.append(0.)
            factorValue = 0.

        last_askp_list.append(askp) if askp is not None else last_askp_list.append(last_askp)
        last_askv_list.append(askv) if askv is not None else last_askv_list.append(last_askv)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        askp = self._getAllHistoricalTickData("AskPrice")
        askv = self._getAllHistoricalTickData("AskVolume")
        volume = self._getAllHistoricalTickData("Volume")
        aincremtv = [self.__incremental_ask_volume(askp[i], askv[i], askp[i+1], askv[i+1]) for i in range(len(askp)-1)]
        incremtv = np.add(aincremtv, volume[1:] / 2)
        if len(incremtv) > 10:
            minv = np.percentile(incremtv, 10)
            maxv = np.percentile(incremtv, 90)
            vcutoff = np.append(np.insert(np.linspace(minv, maxv, self.__n + 1), 0, -np.inf), np.inf)

            density = self.__get_density(incremtv, vcutoff)

            self.__historicalCutoff = vcutoff
            self.__historicalDensity = density

    @staticmethod
    def __get_density(x, cutoff):
        vnum = []
        for i, each in enumerate(cutoff[:-1]):
            vnum.append(np.nansum((x > each) & (x <= cutoff[i + 1])))
        density = np.divide(vnum, np.nansum(vnum))
        return density

    @staticmethod
    def __incremental_ask_volume(lastp, lastv, currentp, currentv):
        if lastp is not None and currentp is not None:
            maxp = min(max(lastp), max(currentp))
            minp = min(min(lastp), min(currentp))
            commonp = np.clip(sorted(set(lastp).union(set(currentp))), a_min=minp, a_max=maxp)
            last_info = dict(zip(lastp, lastv))
            current_info = dict(zip(currentp, currentv))
            lastvn = [last_info.get(each, 0) for each in commonp]
            currentvn = [current_info.get(each, 0) for each in commonp]
            return np.nansum(np.subtract(currentvn, lastvn))
        else:
            return 0.

