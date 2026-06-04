from System.Factor import Factor


class TransActiveAskOrderInfo(Factor):
    def calculate(self):
        trans = self._getLastTickData("Transactions")
        if trans is not None:
            flag = self._getTransactionData("BSFlag", trans)
            trans = trans[flag == 2, :]
            if trans.shape[0] > 0:
                ask_order = self._getTransactionData("AskOrder", trans)
                amt = self._getTransactionData("Amount", trans)
                ask_order_dict = {}
                for i in range(trans.shape[0]):
                    ar = ask_order[i]
                    if ar in ask_order_dict:
                        ask_order_dict[ar] += amt[i]
                    else:
                        ask_order_dict[ar] = amt[i]
                factorValue = ask_order_dict
            else:
                factorValue = None
        else:
            factorValue = None
        self._addFactorValue(factorValue)
