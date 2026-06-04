

__all__ = ['panel_shape', 'stock_list']
from xquant.factordata import FactorData
s = FactorData()
#stock_list = list(s.hset('MARKET','20210930','ALLA_HIS')['stock'])
stock_list = list(s.hset('MARKET','20220725','ALLA_HIS')['stock'])

stock_list = sorted(stock_list)
panel_shape = (-1, len(stock_list))
#print('panel_shape',panel_shape)