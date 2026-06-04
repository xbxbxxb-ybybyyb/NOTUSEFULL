from System.Factor import Factor


class AskDealVolume(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            askOrder = self._getTransactionData("AskOrder", transaction)
            volumeData = self._getTransactionData("Volume", transaction)
            ask_order_dict = {}
            for i in range(transaction.shape[0]):
                ar = askOrder[i]
                if ar in ask_order_dict:
                    ask_order_dict[ar] += volumeData[i]
                else:
                    ask_order_dict[ar] = volumeData[i]
            factorValue = ask_order_dict if ask_order_dict else None
        else:
            factorValue = None

        self._addFactorValue(factorValue)
