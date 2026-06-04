import os
import matplotlib
import numpy as np
import matplotlib.pyplot as plt

from version_control import version_number

import unittest
if version_number == 0:
    import xquant.pydraw as xd
else:
    import xquant.xqutils.xqdraw as xd



class TestDraw(unittest.TestCase):
    def setUp(self):
        open('plot.png', 'w').close()

    def test_demo(self):
        matplotlib.use('Agg')
        xData = np.arange(0, 10, 1)
        yData1 = xData.__pow__(2.0)
        yData2 = np.arange(15, 61, 5)
        with self.assertRaises(Exception) as context:
            plt.figure(num=1, figsize=(8, 6))
            plt.title('Plot 1', size=14)
            plt.xlabel('x-axis', size=14)
            plt.ylabel('y-axis', size=14)
            plt.plot(xData, yData1, color='b', linestyle='--', marker='o', label='y1 data')
            plt.plot(xData, yData2, color='r', linestyle='-', label='y2 data')
            plt.legend(loc='upper left')
            plt.savefig('plot.png', format='png')
        self.assertTrue('DISPLAY' in str(context.exception))

        xd.showfig("plot.png")

    def tearDown(self):
        [os.remove(file) for file in os.listdir('.') if file.endswith('.png')]
