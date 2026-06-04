from System.Factor import Factor


# 按卖方主动成交价格汇总成交量
class AskPVolume(Factor):
    def calculate(self):
        trans = self._getLastTickData("Transactions")
        if trans is not None:
            flag = self._getTransactionData("BSFlag", trans)
            trans = trans[flag == 2, :]
            ask_deal_price = self._getTransactionData("Price", trans)
            ask_deal_volume = self._getTransactionData("Volume", trans)
            ask_price_dict = {}
            for i in range(trans.shape[0]):
                ap = ask_deal_price[i]
                if ap in ask_price_dict:
                    ask_price_dict[ap] += ask_deal_volume[i]
                else:
                    ask_price_dict[ap] = ask_deal_volume[i]
            factorValue = ask_price_dict if ask_price_dict else None
        else:
            factorValue = None
        self._addFactorValue(factorValue)
