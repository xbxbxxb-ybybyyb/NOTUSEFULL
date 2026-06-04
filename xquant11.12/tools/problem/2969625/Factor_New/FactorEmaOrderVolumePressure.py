from System.Factor import Factor


class FactorEmaOrderVolumePressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__emaOrderVolumePressureLag = self._getParameter("EMAOrderVolumePressureLag")
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")

        self.__emaOrderVolumePressure = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__emaOrderVolumePressureLag,
                    "OriginalData": {
                        "ClassName": "OrderVolumePressure",
                        "Parameters": {
                            "NumOrderMax": self.__numOrderMax,
                            "NumOrderMin": self.__numOrderMin,
                            "WeightDecay": self.__weightDecay
                        }
                    }
                }
            }
        )

    def calculate(self):
        factorValue = -self.__emaOrderVolumePressure.getLastFactorValue()

        self._addFactorValue(factorValue)
