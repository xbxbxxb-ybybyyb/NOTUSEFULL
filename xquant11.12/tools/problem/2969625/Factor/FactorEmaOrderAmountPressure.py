from System.Factor import Factor


class FactorEmaOrderAmountPressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__emaOrderAmountPressureLag = self._getParameter("EMAOrderAmountPressureLag")
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")

        self.__emaOrderAmountPressure = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__emaOrderAmountPressureLag,
                    "OriginalData": {
                        "ClassName": "OrderAmountPressure",
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
        factorValue = self.__emaOrderAmountPressure.getLastFactorValue()

        self._addFactorValue(factorValue)
