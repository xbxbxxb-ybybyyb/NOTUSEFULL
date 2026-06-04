from System.Factor import Factor


class LLTFilter(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__a = 2 / (1 + self.__lag)
        self.__obj = self._getFactor(
            {
                "ClassName": self._getParameter("FilterObj")
            }
        )

    def calculate(self):

        objs = self.__obj.getFactorValueList()[-3:]
        llts = self.getFactorValueList()[-3:]
        a = self.__a
        if len(llts) < 3:
            factorValue = objs[-1]
        else:
            factorValue = (a - a * a / 4) * objs[-1] + a * a / 2 * objs[-2] - (a - 3 * a * a / 4) * objs[-3] + \
                  2 * (1 - a) * llts[-1] - (1 - a) ** 2 * llts[-2]

        self._addFactorValue(factorValue)
