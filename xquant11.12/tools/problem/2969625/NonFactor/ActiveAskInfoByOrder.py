from System.Factor import Factor


class ActiveAskInfoByOrder(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:

            bsflag = self._getTransactionData("BSFlag", transaction)
            askr = self._getTransactionData("AskOrder", transaction)[bsflag == 2]
            volume = self._getTransactionData("Volume", transaction)[bsflag == 2]
            amount = self._getTransactionData("Amount", transaction)[bsflag == 2]
            timestamp = self._getTransactionData("Timestamp", transaction)[bsflag == 2]

            ask_order_dict = {}
            for i in range(len(askr)):
                br = askr[i]
                if br in ask_order_dict:
                    ask_order_dict[br][0] += amount[i]
                    ask_order_dict[br][1] += volume[i]
                else:
                    ask_order_dict[br] = [amount[i], volume[i], timestamp[i]]
            factorValue = ask_order_dict if ask_order_dict else None
        else:
            factorValue = None

        self._addFactorValue(factorValue)
