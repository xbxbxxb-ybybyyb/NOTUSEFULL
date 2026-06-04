from System.Factor import Factor


class BidDealAmount(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bidOrder = self._getTransactionData("BidOrder", transaction)
            amountData = self._getTransactionData("Amount", transaction)
            bid_order_dict = {}
            for i in range(transaction.shape[0]):
                br = bidOrder[i]
                if br in bid_order_dict:
                    bid_order_dict[br] += amountData[i]
                else:
                    bid_order_dict[br] = amountData[i]
            factorValue = bid_order_dict if bid_order_dict else None
        else:
            factorValue = None

        self._addFactorValue(factorValue)
