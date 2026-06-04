from System.Factor import Factor
import numpy as np


class TimeWindow(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子参数：ticks in the window
        self.__paraWindowSpan = para['paraWindowSpan']
        factorManagement.registerFactor(self, para)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.timeWindow = {}
        for bin in range(self.__paraWindowSpan):
            if not bin in self.timeWindow :
                self.timeWindow[bin] = {"open": [], "close": [], "high": [], "low": [],
                 "volume": [], "amount": [], "initialTime": [], "endTime": [],
                 "midPrice": []}

    def calculate(self):
        length = min(len(self.__data.getContent()), self.__paraWindowSpan)
        dataWindow = self.__data.getContent()[-length:]
        price = []
        volume = []
        amount = []
        time = []
        for i in range(0, length):
            price.append(dataWindow[i].lastPrice)
            volume.append(dataWindow[i].volume)
            amount.append(dataWindow[i].amount)
            time.append(dataWindow[i].time)

        val = {"open": price[0], "close": price[-1], "high": max(price), "low": min(price),
                                "volume": sum(volume), "amount": sum(amount), "initialTime": time[0], "endTime": time[-1],
                                "midPrice": (price[0] + price[-1]) / 2}

        tick_bin_key = (len(self.__data.getContent()) - 1) % self.__paraWindowSpan
        for key in val:
            self.timeWindow[tick_bin_key][key].append(val[key])

        if len(self.timeWindow[tick_bin_key]["open"]) <= self.__paraWindowSpan:
            for bin in range(self.__paraWindowSpan):
                if tick_bin_key == bin:
                    continue
                for key in val:
                    self.timeWindow[bin][key].append(val[key])

        self.addData(self.timeWindow[tick_bin_key], self.__data.getLastTimeStamp())
