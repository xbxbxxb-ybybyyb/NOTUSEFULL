from System.Factor import Factor


class FactorTransVolumeWeightedSwing(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__MALag = self._getParameter("MALag")
        self.__diffLag = self._getParameter("DiffLag")
        self.__volumeLag = self._getParameter("VolumeLag")

        self.__emaTradeVolumeDiff = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__diffLag,
                    "OriginalData": {
                        "ClassName": "TransVolumeWeightedDiff",
                        "Parameters": {
                            "DecayNum": self.__decayNum,
                            "MALag": self.__MALag
                        }
                    }
                }
            }
        )
        self.__emaTradeVolume = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__volumeLag,
                    "OriginalData": {
                        "ClassName": "TransVolumeWeighted",
                        "Parameters": {
                            "DecayNum": self.__decayNum,
                            "MALag": self.__MALag
                        }
                    }
                }
            }
        )

    def calculate(self):
        diffVolume = self.__emaTradeVolumeDiff.getLastFactorValue()
        tradeVolume = self.__emaTradeVolume.getLastFactorValue()

        if tradeVolume <= 0:
            factorValue = 0
        else:
            factorValue = diffVolume / tradeVolume

        self._addFactorValue(factorValue)
