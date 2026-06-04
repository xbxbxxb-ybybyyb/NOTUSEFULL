import numpy as np
from xquant.pyfile import Pyfile

start_date = "20190701"
end_date = "20190831"

py = Pyfile()

results_buy = py.listdir("Apollo/cv_results/{}-{}_universal/buy/".format(start_date, end_date))
results_sell = py.listdir("Apollo/cv_results/{}-{}_universal/sell/".format(start_date, end_date))

print(len(results_buy))
print(len(results_sell))
print(np.array(results_buy)[~np.in1d(results_buy, results_sell)])
print(np.array(results_sell)[~np.in1d(results_sell, results_buy)])
