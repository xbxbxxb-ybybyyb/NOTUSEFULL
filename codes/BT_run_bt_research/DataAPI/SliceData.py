class SliceData:
    def __init__(self, code=0, timestamp=0, time=0, bid_price=0, ask_price=0, bid_vol=0, ask_vol=0,
                 last_price=0, volume=0, amount=0,
                 total_vol=0, total_amt=0, pre_close=0, transaction_data=[], transaction_timestamp=[],
                 max_price=0, min_price=0, next_timestamp=0, high_price=0, low_price=0):
        self.code = code
        self.timeStamp = timestamp
        self.time = time   # 当日日内的时间，例如103001000代表10:31:01
        self.bidPrice = bid_price
        self.askPrice = ask_price
        self.bidVolume = bid_vol
        self.askVolume = ask_vol
        self.lastPrice = last_price
        self.volume = volume
        self.amount = amount
        self.totalVolume = total_vol
        self.totalAmount = total_amt
        self.previousClosingPrice = pre_close
        self.transactionData = transaction_data
        self.transactionTimeStamp = transaction_timestamp
        self.isLastSlice = False
        self.maxPrice = max_price
        self.minPrice = min_price
        self.highPrice = high_price
        self.lowPrice = low_price
        self.nextTimeStamp = next_timestamp
