from System.Factor import Factor


class FactorActiveVolRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__maLag = self._getParameter("MALag")
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__emaFastTradeVolumeWeighted = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__fastLag,
                    "OriginalData": {
                        "ClassName": "TradeVolumeWeightedEasy",
                        "Parameters": {
                            "DecayNum": self.__decayNum,
                            "MALag": self.__maLag
                        }
                    }
                }
            }
        )

        self.__emaSlowTradeVolumeWeighted = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__slowLag,
                    "OriginalData": {
                        "ClassName": "TradeVolumeWeightedEasy",
                        "Parameters": {
                            "DecayNum": self.__decayNum,
                            "MALag": self.__maLag
                        }
                    }
                }
            }
        )

    def calculate(self):
        fastBidVolume, fastAskVolume = self.__emaFastTradeVolumeWeighted.getLastFactorValue()
        slowBidVolume, slowAskVolume = self.__emaSlowTradeVolumeWeighted.getLastFactorValue()

        netVolume = fastBidVolume - fastAskVolume
        tradeVolume = slowBidVolume + slowAskVolume

        if  tradeVolume <= 0:
            value = 0.0
        else:
            value = netVolume / tradeVolume

        self._addFactorValue(value)






