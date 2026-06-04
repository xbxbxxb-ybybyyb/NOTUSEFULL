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
        self._addIntermediate("CrossPosition", [-1])  # 记录非零的位置，即交叉位置
        self._addIntermediate("BoardCrossPosition", [])
        self._addIntermediate("CrossPointInfo", [])
        self._addIntermediate("PriceEdge", [])
        self._addIntermediate("Ratio1", [])
        self._addIntermediate("Ratio2", [])
        self._addIntermediate("EMARatio", [])
        self._addIntermediate("AveAmplitude", [])

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

        midPriceList = self.__midPrice.getFactorValueList()

        if self.__emaMidPriceFast.getLastFactorValue() > self.__emaMidPriceSlow.getLastFactorValue():
            direction.append(1)
        else:
            direction.append(0)

        if len(direction) > 2:
            directionDiff.append(direction[-1] - direction[-2])
            if directionDiff[-1] != 0:
                if len(crossPosition) >= 2:
                    crossPosition.append(len(directionDiff) - 2)
                else:
                    crossPosition.append(len(directionDiff) - 1)
                boardCrossPosition.append(crossPosition[-1] + 1)
                if len(crossPosition) == 2:
                    if directionDiff[crossPosition[1]] == 1:
                        directionDiff.insert(0, -1)
                        crossPointInfo.append([0, -1, 0])
                        priceEdge.append(midPriceList[crossPointInfo[-1][0]])
                    elif directionDiff[crossPosition[1]] == -1:
                        directionDiff.insert(0, 1)
                        crossPointInfo.append([0, 1, 0])
                        priceEdge.append(midPriceList[crossPointInfo[-1][0]])

                if directionDiff[-1] == 1:
                    price_bottom = min(midPriceList[(crossPosition[-2] + 2):(crossPosition[-1] + 2)])
                    posBegin = (midPriceList[(crossPosition[-2] + 2):(crossPosition[-1] + 2)].index(price_bottom)
                                 + crossPosition[-2]
                                 + 2)
                    crossPointInfo.append([posBegin, 1, (crossPosition[-1]) + 1])
                    priceEdge.append(midPriceList[crossPointInfo[-1][0]])
                    ratio1.append(abs(priceEdge[-1] / priceEdge[-2] - 1) * 1000)
                    ratio2.append(sum(ratio1) / len(ratio1))
                    if len(ratio2) > 5:
                        emaRatio.append(emaRatio[-1] + 2 / 6 * (ratio2[-1] - emaRatio[-1]))
                    elif len(ratio2) > 1:
                        emaRatio.append(emaRatio[-1] + 2 / len(ratio2) * (ratio2[-1] - emaRatio[-1]))
                    else:
                        emaRatio.append(ratio2[0])
                elif directionDiff[-1] == -1:
                    priceTop = max(midPriceList[(crossPosition[-2] + 2):(crossPosition[-1] + 2)])
                    posBegin = (midPriceList[(crossPosition[-2] + 2):(crossPosition[-1] + 2)].index(priceTop)
                                 + crossPosition[-2]
                                 + 2)
                    crossPointInfo.append([posBegin, -1, (crossPosition[-1]) + 1])
                    priceEdge.append(midPriceList[crossPointInfo[-1][0]])
                    ratio1.append(abs(priceEdge[-1] / priceEdge[-2] - 1) * 1000)
                    ratio2.append(sum(ratio1) / len(ratio1))
                    if len(ratio2) > 5:
                        emaRatio.append(emaRatio[-1] + 2 / 6 * (ratio2[-1] - emaRatio[-1]))
                    elif len(ratio2) > 1:
                        emaRatio.append(emaRatio[-1] + 2 / len(ratio2) * (ratio2[-1] - emaRatio[-1]))
                    else:
                        emaRatio.append(ratio2[0])

        if len(midPriceList) <= 1:
            ratioChange = 0
            speedChange = 0
            aveAmplitude.append(0)
        elif len(crossPointInfo) == 0:
            ratioChange = midPriceList[-1] / midPriceList[0] - 1
            speedChange = ratioChange / (len(midPriceList) - 1)
            aveAmplitude.append(0)
        else:
            if len(midPriceList) == boardCrossPosition[-1] + 2:
                aveAmplitude.append(emaRatio[-1])
            else:
                aveAmplitude.append(aveAmplitude[-1])

            if len(midPriceList) == crossPointInfo[len(crossPointInfo) - 1][-1] + 1:
                ratioChange = midPriceList[-1] / midPriceList[crossPointInfo[len(crossPointInfo) - 2][0]] - 1
                speedChange = ratioChange / (len(midPriceList) - crossPointInfo[len(crossPointInfo) - 2][0] - 1)
            else:
                ratioChange = midPriceList[-1] / midPriceList[crossPointInfo[len(crossPointInfo) - 1][0]] - 1
                speedChange = ratioChange / (len(midPriceList) - crossPointInfo[len(crossPointInfo) - 1][0] - 1)

        factorValue = [ratioChange, speedChange, aveAmplitude[-1]]

        self._addFactorValue(factorValue)
