import lightgbm as lgb
from sklearn.datasets import load_boston
data = lgb.Dataset(*load_boston(True))
lgb.train({'device': 'cpu'}, data)  