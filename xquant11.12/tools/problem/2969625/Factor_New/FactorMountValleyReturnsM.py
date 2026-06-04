from System.Factor import Factor


class FactorMountValleyReturnsM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__wd = self._getParameter("Window")

        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1
                }
            }
        )
        self.__mvMidpW = self._getFactor(
            {
                "ClassName": "MountValleyMidpWM",
                "Parameters": {
                    "Grade": 1,
                    "Window": self.__wd
                }
            }
        )

    def calculate(self):

        midpw = self.__midPriceW.getLastFactorValue()
        mvs = self.__mvMidpW.getLastFactorValue()

        factorValue = -(midpw / mvs[1] - 1) * 1e2

        self._addFactorValue(factorValue)
