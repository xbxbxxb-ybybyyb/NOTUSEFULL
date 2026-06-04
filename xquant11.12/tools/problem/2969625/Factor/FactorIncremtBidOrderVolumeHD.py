from System.Factor import Factor
import numpy as np


class FactorIncremtBidOrderVolumeHD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__n = self._getParameter("NumGroups")

        self.__historicalDensity = None
        self.__historicalCutoff = None

        self._addIntermediate("AlternativeDensity", [])
        self._addIntermediate("AlternativeCutoff", [])

        self._addIntermediate("IncremtBidOrderVolumeList", [])
        self._addIntermediate("LastBidPriceList", [])
        self._addIntermediate("LastBidVolumeList", [])

    def calculate(self):

        incremt_bidv_list = self.getIntermediate("IncremtBidOrderVolumeList")
        last_bidp_list = self.getIntermediate("LastBidPriceList")
        last_bidv_list = self.getIntermediate("LastBidVolumeList")
        alternative_density = self.getIntermediate("AlternativeDensity")
        alternative_cutoff = self.getIntermediate("AlternativeCutoff")

        if alternative_density:
            alternative_density.append(alternative_density[-1])
            alternative_cutoff.append(alternative_cutoff[-1])
        else:
            alternative_density.append(None)
            alternative_cutoff.append(None)

        last_bidp = last_bidp_list[-1] if last_bidp_list else None
        last_bidv = last_bidv_list[-1] if last_bidv_list else None
        bidp = self._getLastTickData("BidPrice")
        bidv = self._getLastTickData("BidVolume")
        trans = self._getLastTickData("Transactions")

        if last_bidp is not None and bidp is not None:
            incremt_bidv = self.__incremental_bid_volume(last_bidp, last_bidv, bidp, bidv)

            if trans is not None:
                bsflag = self._getTransactionData("BSFlag", trans)
                volume = self._getTransactionData("Volume", trans)
                incremt_bidv += np.nansum(volume[bsflag == 1])

            incremt_bidv_list.append(incremt_bidv)

            # 历史信息缺失，使用当天前600个Tick信息代替历史分布，后续不变化
            if self.__historicalDensity is None and (len(incremt_bidv_list) > 600) and (alternative_density[-1] is None):
                minv = np.percentile(incremt_bidv_list, 10)
                maxv = np.percentile(incremt_bidv_list, 90)
                vcutoff = np.append(np.insert(np.linspace(minv, maxv, self.__n + 1), 0, -np.inf), np.inf)
                density = self.__get_density(incremt_bidv_list, vcutoff)
                alternative_cutoff[-1] = vcutoff
                alternative_density[-1] = density

            # 计算因子
            historical_density = self.__historicalDensity if self.__historicalDensity is not None else alternative_density[-1]
            historical_cutoff = self.__historicalCutoff if self.__historicalCutoff is not None else alternative_cutoff[-1]

            if historical_density is not None:
                sub_bidv_list = np.array(incremt_bidv_list[-self.__lag:])
                density = self.__get_density(sub_bidv_list, historical_cutoff)

                factorValue = np.sqrt(1 - np.nansum(np.sqrt(historical_density * density)))
                if np.nanmean(sub_bidv_list) < np.nanmedian(historical_cutoff):
                    factorValue = -factorValue
            else:
                factorValue = 0.

        else:
            incremt_bidv_list.append(0.)
            factorValue = 0.

        last_bidp_list.append(bidp) if bidp is not None else last_bidp_list.append(last_bidp)
        last_bidv_list.append(bidv) if bidv is not None else last_bidv_list.append(last_bidv)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        bidp = self._getAllHistoricalTickData("BidPrice")
        bidv = self._getAllHistoricalTickData("BidVolume")
        volume = self._getAllHistoricalTickData("Volume")
        bincremtv = [self.__incremental_bid_volume(bidp[i], bidv[i], bidp[i+1], bidv[i+1]) for i in range(len(bidp)-1)]
        incremtv = np.add(bincremtv, volume[1:] / 2)
        if len(incremtv) > 10:  # 上市第一天或转债前一天开盘临停可能取不到盘口
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
    def __incremental_bid_volume(lastp, lastv, currentp, currentv):
        if lastp is not None and currentp is not None:
            maxp = max(max(lastp), max(currentp))
            minp = max(min(lastp), min(currentp))
            commonp = np.clip(sorted(set(lastp).union(set(currentp))), a_min=minp, a_max=maxp)
            last_info = dict(zip(lastp, lastv))
            current_info = dict(zip(currentp, currentv))
            lastvn = [last_info.get(each, 0) for each in commonp]
            currentvn = [current_info.get(each, 0) for each in commonp]
            return np.nansum(np.subtract(currentvn, lastvn))
        else:
            return 0.

