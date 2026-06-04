import numpy as np
from System.Factor import Factor


class FactorDistanceZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.window = self._getParameter("Window")
        self.shortWindow = self._getParameter("ShortWindow")

        self.quoteVWAP = self._getFactor(
            {
                "ClassName": "QuoteVWAP",
                "Parameters": {
                    "Level": 2
                }
            }
        )

    def _onNewDay(self):
        self._setIntermediate("buyAmt", [])
        self._setIntermediate("sellAmt", [])
        self._setIntermediate("bidVWAP", [])
        self._setIntermediate("askVWAP", [])
        self._setIntermediate("netRatio", [])

    def calculate(self):
        bidvwap, askvwap = self.quoteVWAP.getLastFactorValue()
        bidVWAP = self.getIntermediate("bidVWAP")
        askVWAP = self.getIntermediate("askVWAP")
        bidVWAP.append(bidvwap)
        askVWAP.append(askvwap)

        preclose = self._getLastTickData("PreviousClose")
        highPrice = np.max(askVWAP[-self.window:])
        distance = (highPrice - bidvwap) / preclose * 1000

        buyAmt = self.getIntermediate("buyAmt")
        sellAmt = self.getIntermediate("sellAmt")
        trans = self._getLastTickData("Transactions")
        if trans is None:
            buyAmt.append(0)
            sellAmt.append(0)
        else:
            price = self._getTransactionData("Price", trans)
            volume = self._getTransactionData("Volume", trans)
            bs = self._getTransactionData("BSFlag", trans)
            buyMask = bs == 1
            sellMask = bs == 2
            buyAmt.append((price[buyMask] * volume[buyMask]).sum())
            sellAmt.append((price[sellMask] * volume[sellMask]).sum())

        totalBuyAmt = sum(buyAmt[-self.shortWindow:])
        totalSellAmt = sum(sellAmt[-self.shortWindow:])
        totalAmt = totalBuyAmt + totalSellAmt
        netRatioValue = (totalBuyAmt - totalSellAmt) / totalAmt * 100 if totalAmt > 1e-6 else 0
        netRatio = self.getIntermediate("netRatio")
        netRatio.append(netRatioValue)

        st = np.std(netRatio[-self.window:])
        zs = (netRatioValue - np.mean(netRatio[-self.window:])) / st if st > 1e-6 else 0

        self._addFactorValue(distance * zs)
