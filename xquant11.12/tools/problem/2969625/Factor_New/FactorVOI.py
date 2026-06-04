from System.Factor import Factor


class FactorVOI(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("OrderImbalance", [])

    def calculate(self):
        bidPrice = self._getLastNTickData("BidPrice", 2)
        askPrice = self._getLastNTickData("AskPrice", 2)
        bidVolume = self._getLastNTickData("BidVolume", 2)
        askVolume = self._getLastNTickData("AskVolume", 2)
        if len(bidPrice) <= 1:
            orderImbalance = 0.
        else:
            deltaVB = self._get_delta_volume(bidPrice, bidVolume, "B")
            deltaVA = self._get_delta_volume(askPrice, askVolume, "A")
            deltaSum = abs(deltaVB) + abs(deltaVA)
            orderImbalance = (deltaVB - deltaVA) / deltaSum * 100 if deltaSum != 0. else 0.

        orderImbalanceList = self.getIntermediate("OrderImbalance")
        value = self._EMA_calculate(orderImbalance, orderImbalanceList, self.__lag)
        orderImbalanceList.append(value)

        self._addFactorValue(value)

    def _get_delta_volume(self, price, volume, side):
        P0 = [tick[0] for tick in price]
        V0 = [tick[0] for tick in volume]
        if side == "B":
            if P0[-1] < P0[0]:
                deltaV = 0.
            elif P0[-1] == P0[0]:
                deltaV = V0[-1] - V0[0]
            else:
                deltaV = V0[-1]
        elif side == "A":
            if P0[-1] > P0[0]:
                deltaV = 0.
            elif P0[-1] == P0[0]:
                deltaV = V0[-1] - V0[0]
            else:
                deltaV = V0[-1]
        else:
            deltaV = None
        return deltaV

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])




