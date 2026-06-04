from System.Factor import Factor


class TransDelegateBid1OrderQueue(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self._addIntermediate("QIndexList", [])  # 存储索引，key是订单号，value是队列中的位置

    def calculate(self):
        qindex_list = self.getIntermediate("QIndexList")
        qindex = qindex_list[-1].copy() if len(qindex_list) > 0 else dict()
        lastFactorValue = self.getLastFactorValue()
        bid1q = lastFactorValue.copy() if lastFactorValue is not None else list()  # 买一挂单成交队列

        trans = self._getLastTickData("Transactions")
        if trans is not None:
            flag = self._getTransactionData("BSFlag", trans)
            trans = trans[flag == 2, :]
            if trans.shape[0] > 0:
                bid_order = self._getTransactionData("BidOrder", trans)
                volume = self._getTransactionData("Volume", trans)
                dp = self._getTransactionData("Price", trans)
                tsp = self._getTransactionData("Timestamp", trans)

                for i in range(trans.shape[0]):
                    br = bid_order[i]
                    if br in qindex:
                        idx = qindex[br]
                        bid1q[idx][1] += volume[i]  # 如果存在直接修改
                    else:
                        qindex[br] = len(qindex)
                        bid1q.append([br, volume[i], dp[i], tsp[i]])   # 不存在则新增

        qindex_list.append(qindex)
        self._addFactorValue(bid1q)


