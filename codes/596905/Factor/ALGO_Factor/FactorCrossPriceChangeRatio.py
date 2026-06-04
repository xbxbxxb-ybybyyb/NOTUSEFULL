from System.Factor import Factor


class FactorCrossPriceChangeRatio(Factor):
    def __init__(self, config, factorManager):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        super().__init__(config, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__crossPoint = self._getFactor(
            {
                "ClassName": "CrossPoint",
                "Parameters": {
                    "FastLag": self.__fastLag,
                    "SlowLag": self.__slowLag
                }
            }
        )

    def calculate(self):
        factorValue = self.__crossPoint.getLastFactorValue()[0]

        self._addFactorValue(factorValue)
