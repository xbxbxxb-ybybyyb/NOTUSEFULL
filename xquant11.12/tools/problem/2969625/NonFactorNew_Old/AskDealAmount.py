from System.Factor import Factor


class AskDealAmount(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            askOrder = self._getTransactionData("AskOrder", transaction)
            amountData = self._getTransactionData("Amount", transaction)

            ask_order_dict = {}
            for i in range(transaction.shape[0]):
                ar = askOrder[i]
                if ar in ask_order_dict:
                    ask_order_dict[ar] += amountData[i]
                else:
                    ask_order_dict[ar] = amountData[i]
            factorValue = ask_order_dict if ask_order_dict else None
        else:
            factorValue = None

        self._addFactorValue(factorValue)
