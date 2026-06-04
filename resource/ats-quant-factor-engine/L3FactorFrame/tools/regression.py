import math
import numpy as np
from numba import jit, njit

def demo(X, y):
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

    # 创建线性回归模型
    model = LinearRegression()

    # 训练模型
    model.fit(X, y)

    # 预测
    y_pred = model.predict(X)

    # 计算斜率（回归系数）和截距
    slope = model.coef_[0]
    intercept = model.intercept_

    # 计算R方
    r_squared = r2_score(y, y_pred)

    print(f"斜率 (回归系数): {slope}")
    print(f"截距: {intercept}")
    print(f"R方 (决定系数): {r_squared}")
    print(f"R (决定系数): {np.sqrt(r_squared)}")




@jit(nopython = True)
def simpleRegression(X, Y):
    xbar = 0
    ybar = 0
    sumXX = 0
    sumXY = 0
    sumYY = 0
    sumX = 0
    sumY = 0
    sumerror = 0
    for i in range(1,len(X)+1, 1):
        x = X[i-1]
        y = Y[i-1]
        if i==1:
            xbar = x
            ybar = y
            sumX += x
            sumY += y
        else:
            fact1 = i
            fact2 = (i-1.0) / i
            dx = x - xbar
            dy = y - ybar
            sumXX += dx * dx * fact2
            sumYY += dy * dy * fact2
            sumXY += dx * dy * fact2
            xbar += dx / fact1
            ybar += dy / fact1
            sumX += x
            sumY += y


    if abs(sumXX) < 1e-10 or abs(sumYY)<1e-10:
        return 0
    else:
        slope = sumXY / sumXX
    ssto = sumYY
    sumerror =  max(0.0, sumYY - sumXY * sumXY / sumXX)
    R2 = (ssto - sumerror) / ssto

    result = math.sqrt(R2)
    if slope < 0:
        result = -result
    return result



class SimpleRegression:
    def __init__(self, include_intercept=True):
        self.hasIntercept = include_intercept
        self.clear()


    def addData(self, x:float, y:float):
        if self.n == 0:
            self.xbar = x
            self.ybar = y
        else:
            if self.hasIntercept:
                fact1 = 1.0 + self.n
                fact2 = self.n / (1.0 + self.n)
                dx = x - self.xbar
                dy = y - self.ybar
                self.sumXX += dx * dx * fact2
                self.sumYY += dy * dy * fact2
                self.sumXY += dx * dy * fact2
                self.xbar += dx / fact1
                self.ybar += dy / fact1

        if not self.hasIntercept:
            self.sumXX += x * x
            self.sumYY += y * y
            self.sumXY += x * y

        self.sumX += x
        self.sumY += y
        self.n += 1

    def clear(self):
        self.sumX = 0
        self.sumXX = 0
        self.sumY = 0
        self.sumYY = 0
        self.sumXY = 0
        self.n = 0

    def getSlope(self):
        if self.n < 2:
            return float('nan')  # Not enough data
        if abs(self.sumXX) < 10 * np.finfo(float).eps:
            return float('nan')  # Not enough variation in x
        return self.sumXY / self.sumXX

    def getR(self):
        slope = self.getSlope()
        result = math.sqrt(self.getRSquare())
        if slope < 0:
            result = -result
        return result

    def getRSquare(self):
        ssto = self.getTotalSumSquares()
        return (ssto - self.getSumSquaredErrors()) / ssto

    def getN(self):
        return self.n

    def getTotalSumSquares(self):
        if self.n < 2:
            return float('nan')
        return self.sumYY

    def getSumSquaredErrors(self):
        if abs(self.sumXX) < np.finfo(float).eps:
            return float('nan')
        return max(0.0, self.sumYY - self.sumXY * self.sumXY / self.sumXX)

    def getIntercept(self, slope=None):
        if self.hasIntercept:
            if self.n == 0:
                return float('nan')
            if slope is None:
                slope = self.getSlope()
            return (self.sumY - slope * self.sumX) / self.n
        return 0.0

    def append(self, reg):
        if self.n == 0:
            self.xbar = reg.xbar
            self.ybar = reg.ybar
            self.sumXX = reg.sumXX
            self.sumYY = reg.sumYY
            self.sumXY = reg.sumXY
        else:
            if self.hasIntercept:
                fact1 = reg.n / (reg.n + self.n)
                fact2 = self.n * reg.n / (reg.n + self.n)
                dx = reg.xbar - self.xbar
                dy = reg.ybar - self.ybar
                self.sumXX += reg.sumXX + dx * dx * fact2
                self.sumYY += reg.sumYY + dy * dy * fact2
                self.sumXY += reg.sumXY + dx * dy * fact2
                self.xbar += dx * fact1
                self.ybar += dy * fact1
            else:
                self.sumXX += reg.sumXX
                self.sumYY += reg.sumYY
                self.sumXY += reg.sumXY

        self.sumX += reg.sumX
        self.sumY += reg.sumY
        self.n += reg.n

    def __str__(self):
        return f'SimpleRegression(n={self.n}, sumX={self.sumX}, sumXX={self.sumXX}, sumY={self.sumY}, sumYY={self.sumYY}, sumXY={self.sumXY})'

if __name__=="__main__":
    X = np.array([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]]).astype(float)
    y = np.array([3, 4, 2, 5, 6, 7, 8, 7, 10, 12]).astype(float)
    # X = 2 * np.random.rand(100, 1)  # 生成100个随机的X值，范围在0到2之间
    # y = 4 + 3 * X + np.random.randn(100, 1)


    demo(X, y)
    X = X.reshape(1, -1)[0]
    y = -y.reshape(1, -1)[0]
    print(simpleRegression(X, y))
    regression = SimpleRegression()
    for i in range(len(X)):
        regression.addData(X[i], y[i])
        print("===================================")
        print("Slope:", regression.getSlope())
        print("Intercept:", regression.getIntercept())
        print("R^2:", regression.getRSquare())
        print("R:", regression.getR())