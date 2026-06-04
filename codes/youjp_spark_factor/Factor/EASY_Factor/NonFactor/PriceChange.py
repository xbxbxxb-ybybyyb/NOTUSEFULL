from System.Factor import Factor


class PriceChange(Factor):
    def __init__(self, para, factorManager):
        super().__init__(para, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )       

        self.__boardPoint = self._getFactor(
            {
                "ClassName": "BoardPoint",
                "Parameters": {
                    "FastLag": self.__fastLag,
                    "SlowLag": self.__slowLag
                }
            }
        )

    def calculate(self):
        boardPointInfo = self.__boardPoint.getLastFactorValue()
        midPriceList = self.__midPrice.getFactorValueList()

        rate, speed = self._calculate_price_change(boardPointInfo, midPriceList)

        factorValue = [rate, speed]

        self._addFactorValue(factorValue)

    @staticmethod
    def _calculate_price_change(boardPointInfo, midPriceList):
        size = len(midPriceList)
        size_board = len(boardPointInfo)

        price_change_rate, price_change_speed = 0., 0.

        if size > 1:
            if size_board == 0:
                temp = float(midPriceList[-1]) / midPriceList[0] - 1.
                price_change_rate = temp
                price_change_speed = temp * 20.0 / (size - 1)

            elif size_board >= 2:
                if size == boardPointInfo[-1][-1] + 1:
                    temp = float(midPriceList[-1]) / midPriceList[boardPointInfo[-2][0]] - 1.
                    price_change_rate = temp
                    price_change_speed = temp * 20.0 / (size - 1 - boardPointInfo[-2][0])
                else:
                    temp = float(midPriceList[-1]) / midPriceList[boardPointInfo[-1][0]] - 1.
                    price_change_rate = temp
                    price_change_speed = temp * 20.0 / (size - 1 - boardPointInfo[-1][0])

        return price_change_rate, price_change_speed



