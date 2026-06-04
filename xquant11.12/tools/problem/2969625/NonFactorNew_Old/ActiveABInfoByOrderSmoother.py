from System.Factor import Factor
# 一定程度解决大单跨Tick成交问题
# 平滑


class ActiveABInfoByOrderSmoother(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__target = self._getParameter("Target")
        self.__obj = self._getFactor(
            {
                "ClassName": self._getParameter("SmoothObject"),
            }
        )

        if self.__target == "Amount":
            self.__idx = 0
        elif self.__target == "Volume":
            self.__idx = 1
        else:
            raise Exception("Unsupported target.")

    def calculate(self):

        info_by_order = self.__obj.getFactorValueList()[-self.__lag:]

        target_dict = {}
        for orders in info_by_order:
            if orders is not None:
                for br, each in orders.items():
                    if br in target_dict:
                        target_dict[br] += each[self.__idx]
                    else:
                        target_dict[br] = each[self.__idx]

        self._addFactorValue(target_dict)
