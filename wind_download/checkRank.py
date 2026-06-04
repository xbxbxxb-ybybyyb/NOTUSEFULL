from xquant.marketdata import MarketData
mdp = MarketData()
df = mdp.get_data_by_time_frame("Stock", "000001.SZ", "20180301 093000000", "20180305 150000250",["3"], sort_by_receive_time=True)
df = mdp.get_data_by_time_frame("Stock", "000001.SZ", "20180301 093000000", "20180305 150000250", ["2","3"])
df = mdp.get_data_by_time_frame("Index", "000001.SH", "20180301 093000000", "20180305 150000250")
df = mdp.get_data_by_time_frame("Transaction", "000001.SZ", "20180301 093000000", "20180305 150000250")
df = mdp.get_data_by_time_frame("Order", "000001.SZ", "20180301 093000000", "20180305 150000250")