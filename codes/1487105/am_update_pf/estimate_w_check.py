from xquant.xqutils.helper import link
import datetime 
lm = link.LinkMessage()
today = datetime.date.today().strftime('%Y%m%d')

from xquant.factordata import FactorData
s=FactorData()
tomorrow = s.tradingday(today,2)[1]
weight500  = s.hset('INDEX',tomorrow,'ZZ500',1)
lm.sendMessage('ZZ500:'+str(weight500['weight'].sum()))

weight500  = s.hset('INDEX',tomorrow,'HS300',1)
lm.sendMessage('HS300:'+str(weight500['weight'].sum()))