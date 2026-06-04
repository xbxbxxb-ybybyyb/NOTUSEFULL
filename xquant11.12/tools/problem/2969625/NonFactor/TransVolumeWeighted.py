from System.Factor import Factor


class TransVolumeWeighted(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__MALag = self._getParameter("MALag")

        self.__tradeVolumeWeighted = self._getFactor(
            {
                "ClassName": "TradeVolumeWeighted",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__MALag
                }
            }
        )

    def calculate(self):
        volumeBid, volumeAsk = self.__tradeVolumeWeighted.getLastFactorValue()

        if volumeBid < 0 or volumeAsk < 0:
            factorValue = 0
        else:
            factorValue = volumeBid + volumeAsk

        self._addFactorValue(factorValue)
