from System.Factor import Factor


class TransDelegateAsk1OrderQueue(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self._addIntermediate("QIndexList", [])   # 存储索引，key是订单号，value是队列中的位置

    def calculate(self):
        qindex_list = self.getIntermediate("QIndexList")
        qindex = qindex_list[-1].copy() if len(qindex_list) > 0 else dict()
        lastFactorValue = self.getLastFactorValue()
        ask1q = lastFactorValue.copy() if lastFactorValue is not None else list()   # 卖一挂单成交队列

        trans = self._getLastTickData("Transactions")
        if trans is not None:
            flag = self._getTransactionData("BSFlag", trans)
            trans = trans[flag == 1, :]
            if trans.shape[0] > 0:
                ask_order = self._getTransactionData("AskOrder", trans)
                volume = self._getTransactionData("Volume", trans)
                dp = self._getTransactionData("Price", trans)
                tsp = self._getTransactionData("Timestamp", trans)

                for i in range(trans.shape[0]):
                    ar = ask_order[i]
                    if ar in qindex:
                        idx = qindex[ar]
                        ask1q[idx][1] += volume[i]  # 如果存在直接修改
                    else:
                        qindex[ar] = len(qindex)
                        ask1q.append([ar, volume[i], dp[i], tsp[i]])  # 不存在则新增

        qindex_list.append(qindex)
        self._addFactorValue(ask1q)


