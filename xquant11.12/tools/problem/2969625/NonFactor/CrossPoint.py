from System.Factor import Factor


class CrossPoint(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__emaMidPriceFast = self._getFactor(
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
        self.__emaMidPriceSlow = self._getFactor(
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

        self._addIntermediate("Direction", [])
        self._addIntermediate("DirectionDiff", [])
        self._addIntermediate("CrossPosition", [])  # 记录非零的位置，即交叉位置
        self._addIntermediate("BoardCrossPosition", [])
        self._addIntermediate("CrossPointInfo", [])
        self._addIntermediate("PriceEdge", [])
        self._addIntermediate("Ratio1", [])
        self._addIntermediate("Ratio2", [])
        self._addIntermediate("EMARatio", [])
        self._addIntermediate("AveAmplitude", [])
        self._addIntermediate("FirstRealDirectionDiff", [])

    def calculate(self):
        direction = self.getIntermediate("Direction")
        directionDiff = self.getIntermediate("DirectionDiff")
        crossPosition = self.getIntermediate("CrossPosition")
        boardCrossPosition = self.getIntermediate("BoardCrossPosition")
        crossPointInfo = self.getIntermediate("CrossPointInfo")
        priceEdge = self.getIntermediate("PriceEdge")
        ratio1 = self.getIntermediate("Ratio1")
        ratio2 = self.getIntermediate("Ratio2")
        emaRatio = self.getIntermediate("EMARatio")
        aveAmplitude = self.getIntermediate("AveAmplitude")
        firstRealDirectionDiff = self.getIntermediate("FirstRealDirectionDiff")

        midPriceList = self.__midPrice.getFactorValueList()

        if self.__emaMidPriceFast.getLastFactorValue() > self.__emaMidPriceSlow.getLastFactorValue():
            direction.append(1)
        else:
            direction.append(0)

        if len(midPriceList) <= 2:
            directionDiff.append(None)
            firstRealDirectionDiff.append(None)
            crossPosition.append(-1)
            boardCrossPosition.append(None)
            crossPointInfo.append(None)
            priceEdge.append(midPriceList[0])
            ratio1.append(None)
            ratio2.append(None)
            emaRatio.append(None)
        else:
            directionDiff.append(direction[-1] - direction[-2])
            if firstRealDirectionDiff[-1] is None and directionDiff[-1] != 0:  # 记录第一个真正的交叉点的方向
                firstRealDirectionDiff.append(directionDiff[-1])
            else:
                firstRealDirectionDiff.append(firstRealDirectionDiff[-1])
            if directionDiff[-1] == 0:
                crossPosition.append(None)
                boardCrossPosition.append(None)
                crossPointInfo.append(None)
                priceEdge.append(None)
                ratio1.append(None)
                ratio2.append(None)
                emaRatio.append(None)
            else:
                crossPosition.append(len(directionDiff) - 3)
                boardCrossPosition.append(crossPosition[-1] + 1)

                validCrossPosition = self.__getLastNValidValue(crossPosition, 2)
                if directionDiff[-1] == 1:
                    priceRef = min(midPriceList[(validCrossPosition[-2] + 2):(validCrossPosition[-1] + 2)])
                else:
                    priceRef = max(midPriceList[(validCrossPosition[-2] + 2):(validCrossPosition[-1] + 2)])
                posBegin = (midPriceList[(validCrossPosition[-2] + 2):(validCrossPosition[-1] + 2)].index(priceRef) + validCrossPosition[-2] + 2)
                crossPointInfo.append([posBegin, 1, (validCrossPosition[-1]) + 1])
                priceEdge.append(midPriceList[posBegin])
                validPriceEdge = self.__getLastNValidValue(priceEdge, 2)
                ratio1.append(abs(validPriceEdge[-1] / validPriceEdge[-2] - 1) * 1000)
                validRatio1 = self.__getAllValidValue(ratio1)
                ratio2.append(sum(validRatio1) / len(validRatio1))
                validRatio2 = self.__getAllValidValue(ratio2)
                validEmaRatio = self.__getLastNValidValue(emaRatio, 2)
                if len(validRatio2) > 5:
                    emaRatio.append(validEmaRatio[-1] + 2 / 6 * (validRatio2[-1] - validEmaRatio[-1]))
                elif len(validRatio2) > 1:
                    emaRatio.append(validEmaRatio[-1] + 2 / len(validRatio2) * (validRatio2[-1] - validEmaRatio[-1]))
                else:
                    emaRatio.append(validRatio2[0])

        if len(midPriceList) <= 1:
            ratioChange = 0
            speedChange = 0
            aveAmplitude.append(0)
        elif firstRealDirectionDiff[-1] is None:   # 第一个真正的交叉点之前
            ratioChange = midPriceList[-1] / midPriceList[0] - 1
            speedChange = ratioChange / (len(midPriceList) - 1)
            aveAmplitude.append(0)
        else:
            if len(midPriceList) == self.__getLastNValidValue(boardCrossPosition, 1)[-1] + 2:
                aveAmplitude.append(self.__getLastNValidValue(emaRatio, 1)[-1])
            else:
                aveAmplitude.append(aveAmplitude[-1])

            validCrossPointInfo = self.__getAllValidValue(crossPointInfo)
            validCrossPointInfo.insert(0, [0, - firstRealDirectionDiff[-1], 0])

            if len(midPriceList) == validCrossPointInfo[-1][-1] + 1:
                ratioChange = midPriceList[-1] / midPriceList[validCrossPointInfo[-2][0]] - 1
                speedChange = ratioChange / (len(midPriceList) - validCrossPointInfo[-2][0] - 1)
            else:
                ratioChange = midPriceList[-1] / midPriceList[validCrossPointInfo[-1][0]] - 1
                speedChange = ratioChange / (len(midPriceList) - validCrossPointInfo[-1][0] - 1)

        factorValue = [ratioChange, speedChange, aveAmplitude[-1]]

        self._addFactorValue(factorValue)

    def __getLastNValidValue(self, valueList, n):
        validValueList = []
        for i in range(len(valueList) - 1, -1, -1):
            if valueList[i] is not None:
                validValueList.insert(0, valueList[i])
            if len(validValueList) >= n:
                break
        return validValueList

    def __getAllValidValue(self, valueList):
        validValueList = list(filter(lambda x: x is not None, valueList))
        return validValueList
