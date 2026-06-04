# -*- coding: utf-8 -*-
"""
Created on 2017/9/5 13:41

@author: 006547
"""
import time


class ProgressBar:
    def __init__(self, count=0, total=0, width=50):
        self.count = count
        self.total = total
        self.width = width
        self.timeStampStart = time.time()
        self.timeStampLast = time.time()

    def move(self, total):
        self.count += 1
        self.total = total

    def log(self):
        if time.time() - self.timeStampLast >= 5:
            print(' ' * (self.width + 31) + '\r', end='', flush=True)
            self.timeStampLast = time.time()
            timeSpend = self.timeStampLast - self.timeStampStart
            timeRemain = round(timeSpend / self.count * (self.total - self.count) / 60, 2)
            progress = int(self.width * self.count / self.total)
            print('{0:3}%: '.format(int(self.count / self.total * 100)), end='', flush=False)
            print('|' * progress + '-' * (self.width - progress) + ' ', end='', flush=False)
            print("Remaining Time: {0:4}".format(timeRemain) + " min\r", end='', flush=True)
            if progress == self.width:
                print('')
