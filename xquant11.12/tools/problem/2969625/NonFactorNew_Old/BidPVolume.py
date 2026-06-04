from System.Factor import Factor


# 按买方主动价格汇总成交量
class BidPVolume(Factor):
    def calculate(self):
        trans = self._getLastTickData("Transactions")
        if trans is not None:
            flag = self._getTransactionData("BSFlag", trans)
            trans = trans[flag == 1, :]
            bid_deal_price = self._getTransactionData("Price", trans)
            bid_deal_volume = self._getTransactionData("Volume", trans)
            bid_price_dict = {}
            for i in range(trans.shape[0]):
                bp = bid_deal_price[i]
                if bp in bid_price_dict:
                    bid_price_dict[bp] += bid_deal_volume[i]
                else:
                    bid_price_dict[bp] = bid_deal_volume[i]
            factorValue = bid_price_dict if bid_price_dict else None
        else:
            factorValue = None
        self._addFactorValue(factorValue)
