from System.Factor import Factor


class BoardPoint(Factor):
    def __init__(self, para, factorManager):
        super().__init__(para, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

        self.__fastMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__fastLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

        self.__slowMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__slowLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

    def calculate(self):
        midPriceList = self.__midPrice.getFactorValueList()
        fastMidPriceList = self.__fastMidPrice.getFactorValueList()
        slowMidPriceList = self.__slowMidPrice.getFactorValueList()

        value = self._calulate_board_point(midPriceList, fastMidPriceList, slowMidPriceList)
        
        self._addFactorValue(value)

    @staticmethod
    def _calulate_board_point(midPriceList, fastMidPriceList, slowMidPriceList):
        
        boardPointInfo = []

        if len(midPriceList)  < 2:
            return boardPointInfo

        direction = [] #记录快慢线相对大小
        direction2 = [] #判断快慢线交叉情况
        for i in range(len(slowMidPriceList)):
            if fastMidPriceList[i] > slowMidPriceList[i]:
                direction.append(1)
            else:
                direction.append(0)

        non_zero_idx_direction2 = [] #记录非零的位置，即交叉位置

        for i in range(1, len(direction)):
            temp = direction[i] - direction[i-1]
            direction2.append(temp)
            if temp != 0:
                non_zero_idx_direction2.append(len(direction2)-1) #这里对齐的是direction2

        if len(non_zero_idx_direction2) == 0:
            return boardPointInfo

        if len(non_zero_idx_direction2) > 0:
            if direction2[non_zero_idx_direction2[0]] == 1: #?在头部插入-1/1？
                direction2.insert(0, -1)
                boardPointInfo.append([0, -1, 0])
            elif direction2[non_zero_idx_direction2[0]] == -1:
                direction2.insert(0, 1)
                boardPointInfo.append([0, 1, 0])
        
        non_zero_idx_direction2.insert(0, -1)
        
        for i in range(1, len(non_zero_idx_direction2)):
            if direction2[non_zero_idx_direction2[i]+1] == 1:
                min_price = min(midPriceList[(non_zero_idx_direction2[i-1]+2):(non_zero_idx_direction2[i]+2)])
                start_position = midPriceList[(non_zero_idx_direction2[i-1]+2):(non_zero_idx_direction2[i]+2)].index(min_price) + non_zero_idx_direction2[i-1] + 2
                boardPointInfo.append([start_position, 1, (non_zero_idx_direction2[i]+1)])

            elif direction2[non_zero_idx_direction2[i]+1] == -1:
                max_price = max(midPriceList[(non_zero_idx_direction2[i-1]+2):(non_zero_idx_direction2[i]+2)])
                start_position = midPriceList[(non_zero_idx_direction2[i-1]+2):(non_zero_idx_direction2[i]+2)].index(max_price) + non_zero_idx_direction2[i-1] + 2
                boardPointInfo.append([start_position, -1, (non_zero_idx_direction2[i]+1)])

        return boardPointInfo