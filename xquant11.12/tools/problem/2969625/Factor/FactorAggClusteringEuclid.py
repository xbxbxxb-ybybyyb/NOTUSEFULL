import numpy as np
from System.Factor import Factor
from sklearn.cluster import AgglomerativeClustering


class FactorAggClusteringEuclid(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lags = self._getParameter("Lags")
        self.__mlags = self._getParameter("MinuteLags")
        self.__mstep = self._getParameter("MinuteStep")
        self.__nc = self._getParameter("NumClusters")
        self.__hisClusters = None

    def calculate(self):
        import datetime as dt
        time = self._getLastTickData("Timestamp")
        time = dt.datetime.strftime(dt.datetime.fromtimestamp(time),'%H%M%S')
        if time == '093506':
            print('!')
        tlastp = self._getAllTodayTickData("LastPrice")
        treturns = []
        for lag in self.__lags:
            treturns.append((tlastp[-1] / tlastp[-min(len(tlastp), lag)] - 1) * 1e2)
        treturns = np.asarray(treturns)

        if self.__hisClusters is not None:

            mreturns, vreturns, centers, greturns = self.__hisClusters
            x = (treturns - mreturns) / vreturns
            label = int(np.nanargmin([np.nansum(np.power(x - centers[i], 2)) for i in range(len(centers))]))
            factorValue = np.nanmean(greturns[label])

            if np.isnan(factorValue):
                factorValue = 0.
        else:
            w = np.array(self.__lags)[::-1] / np.nansum(self.__lags)
            factorValue = np.nansum(w * treturns)

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        closep = self._getAllMinuteData("ClosePrice")
        mdate = self._getAllMinuteData("Date")

        returns = []
        maxlag = max(self.__mlags)
        for mlag in self.__mlags:
            returns.append(list((closep[maxlag:-self.__mstep] / closep[maxlag-mlag: -self.__mstep-mlag] - 1) * 1e2))
        returns = np.asarray(returns)
        preturns = (closep[maxlag+self.__mstep:] / closep[maxlag:-self.__mstep] - 1) * 1e2
        idx = mdate[maxlag:-self.__mstep] == mdate[:-self.__mstep-maxlag]  # 剔除跨日收益
        returns = returns[:, idx].T
        preturns = preturns[idx]

        mreturns = np.nanmean(returns, axis=0)
        vreturns = np.nanstd(returns, axis=0)
        X = (returns - mreturns) / vreturns  # 标准化

        idx = np.all(~np.isnan(X), axis=1)
        X = X[idx, :]
        returns = returns[idx, :]
        preturns = preturns[idx]

        if len(X) > 1:
            # skearn
            ac = AgglomerativeClustering(n_clusters=self.__nc, affinity="euclidean", linkage="ward", compute_full_tree=False)
            clustering = ac.fit(X)
            labels = clustering.labels_
            centers = [np.nanmean(returns[labels == i, :], axis=0) for i in sorted(set(labels))]
            greturns = [preturns[labels == i] for i in sorted(set(labels))]

            # self
            # labels = self.__agglomerative_clustering(X)
            # centers = [np.nanmean(returns[each], axis=0) for each in labels.values()]
            # greturns = [preturns[each] for each in labels.values()]

            clusters = (mreturns, vreturns, centers, greturns)
        else:
            clusters = None  # 如果历史上分钟数据都缺失

        self.__hisClusters = clusters

    def __agglomerative_clustering(self, X):
        nodes = {i: {"x": X[i], "left": None, "right": None, "n": 1} for i in range(X.shape[0])}  # 存储结点依赖关系
        parent_nodes = list(range(X.shape[0]))  # 存储当前父节点

        # 计算距离
        x_norm2 = np.tile(np.nansum(np.power(X, 2), axis=1), (X.shape[0], 1))
        distances = x_norm2.T + x_norm2 - 2 * np.dot(X, X.T)

        # 聚类
        currentclustid = len(parent_nodes)
        while len(parent_nodes) > self.__nc:
            distances[np.tril_indices(distances.shape[0])] = np.inf
            row_idx, col_idx = self.__minumum(distances)  # location
            idi, idj = parent_nodes[row_idx], parent_nodes[col_idx]
            new_n = nodes[idi]["n"] + nodes[idj]["n"]
            new_node = {"x": None, "left": idi, "right": idj, "n": new_n}

            parent_nodes.remove(idi)
            parent_nodes.remove(idj)

            remain_idx = [each for each in range(len(distances)) if each not in [row_idx, col_idx]]
            di = np.fmin(distances[row_idx, remain_idx], distances[remain_idx, row_idx])
            dj = np.fmin(distances[col_idx, remain_idx], distances[remain_idx, col_idx])
            dij = distances[row_idx, col_idx]

            add_distances = np.array([self.__ward_linkage(nodes, idi, idj, pn, di[k], dj[k], dij) for k, pn in enumerate(parent_nodes)])
            distances = np.vstack((np.hstack((distances[remain_idx][:, remain_idx], add_distances.reshape(-1, 1))), np.ones(len(remain_idx) + 1) * np.inf))

            nodes[currentclustid] = new_node
            parent_nodes.append(currentclustid)
            currentclustid += 1

        # 分组信息
        members = {}
        for i, pn in enumerate(parent_nodes):
            members[i] = self.__travel(pn, nodes, [])
        return members

    def __travel(self, pn, nodes, members):
        ni = nodes[pn]["left"]
        nj = nodes[pn]["right"]
        if ni is None and nj is None:
            members.append(pn)
        elif ni is None:
            self.__travel(nj, nodes, members)
        elif nj is None:
            self.__travel(ni, nodes, members)
        else:
            self.__travel(ni, nodes, members)
            self.__travel(nj, nodes, members)
        return members

    @staticmethod
    def __minumum(distances):
        col_idx = np.nanargmin(distances, axis=1)
        row_idx = np.nanargmin(distances[(range(distances.shape[0]), col_idx)])
        return int(row_idx), int(col_idx[row_idx])

    @staticmethod
    def __ward_linkage(nodes, i, j, k, dik, djk, dij):
        node_i = nodes[i]
        node_j = nodes[j]
        node_k = nodes[k]
        ni = node_i["n"]
        nj = node_j["n"]
        nk = node_k["n"]
        n = ni + nj + nk
        dijk = ((ni + nk) * dik + (nj + nk) * djk - nk * dij) / n
        return dijk

