from System.Factor import Factor


# 买方主动成交按委托订单号记录每一笔成交额信息
class TransActiveBidOrderInfo(Factor):
    def calculate(self):
        trans = self._getLastTickData("Transactions")
        if trans is not None:
            flag = self._getTransactionData("BSFlag", trans)
            trans = trans[flag == 1, :]
            if trans.shape[0] > 0:
                bid_order = self._getTransactionData("BidOrder", trans)
                amt = self._getTransactionData("Amount", trans)
                bid_order_dict = {}
                for i in range(trans.shape[0]):
                    br = bid_order[i]
                    if br in bid_order_dict:
                        bid_order_dict[br] += amt[i]
                    else:
                        bid_order_dict[br] = amt[i]
                factorValue = bid_order_dict
            else:
                factorValue = None
        else:
            factorValue = None
        self._addFactorValue(factorValue)
