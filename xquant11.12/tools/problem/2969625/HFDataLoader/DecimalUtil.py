#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/3/8 13:22
roundingFactor = 10**7
EPSILON = 1.0 / roundingFactor


def isEqual(x, y):
    return abs(x - y) < EPSILON

def greaterThan(x, y):
    return x - y > EPSILON

def lessThan(x, y):
    return y - x > EPSILON

def equalGreaterThan(x, y):
    return greaterThan(x, y) or isEqual(x, y)

def equalLessThan(x, y):
    return lessThan(x, y) or isEqual(x, y)

def isBetween(y, x, z):
    return equalGreaterThan(y, x) and equalLessThan(y, z)

def isZero(x):
    return isEqual(x, 0.)

def myRound(value: float, n: int):
    scale = 1
    for i in range(n):
        scale *= 10
    value = int(value * scale + 0.5 + EPSILON) / scale
    return value