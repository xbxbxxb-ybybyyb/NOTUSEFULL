from System.Factor import Factor


class ActiveBidInfoByOrder(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:

            bsflag = self._getTransactionData("BSFlag", transaction)
            bidr = self._getTransactionData("BidOrder", transaction)[bsflag == 1]
            volume = self._getTransactionData("Volume", transaction)[bsflag == 1]
            amount = self._getTransactionData("Amount", transaction)[bsflag == 1]
            timestamp = self._getTransactionData("Timestamp", transaction)[bsflag == 1]

            bid_order_dict = {}
            for i in range(len(bidr)):
                br = bidr[i]
                if br in bid_order_dict:
                    bid_order_dict[br][0] += amount[i]
                    bid_order_dict[br][1] += volume[i]
                else:
                    bid_order_dict[br] = [amount[i], volume[i], timestamp[i]]
            factorValue = bid_order_dict if bid_order_dict else None
        else:
            factorValue = None

        self._addFactorValue(factorValue)
