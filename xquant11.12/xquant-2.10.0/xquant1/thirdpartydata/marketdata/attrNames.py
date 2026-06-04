#维护需要展示的字段
class SecurityTypeName(object):
    #逐笔成交
    MDTransactionAttrNames = ["MDDate","MDTime","SecurityType","TradeIndex","TradeBuyNo","TradeSellNo","TradeType","TradeBSFlag","TradePrice",
                    "TradeQty","TradeMoney","HTSCSecurityID", "ReceiveDateTime"]
    #一般tick数据
    MDTickAttrNames = ["MDDate","MDTime","SecurityType","PreClosePx","NumTrades","TotalVolumeTrade","TotalValueTrade","LastPx","OpenPx",
                       "HighPx","LowPx","MaxPx","MinPx","HTSCSecurityID","ReceiveDateTime"]

    #基金
    MDFundAttNames = ['MDDate', 'MDTime', 'Symbol', 'PreClosePx', 'NumTrades',
                      'TotalVolumeTrade', 'TotalValueTrade', 'LastPx', 'OpenPx',
                      'ClosePx', 'HighPx', 'LowPx', 'DiffPx1', 'DiffPx2', 'MaxPx',
                      'MinPx', 'TotalBidQty', 'TotalOfferQty', 'IOPV', 'PreIOPV',
                      'BuyNumber', 'BuyAmount', 'BuyMoney', 'SellNumber', 'SellAmount',
                      'SellMoney']

    #黄金
    MDSpotAttNames = ['MDDate', 'MDTime', 'SecurityType', 'SecuritySubType',
                      'SecurityID', 'SecurityIDSource', 'Symbol', 'MDLevel',
                      'MDChannel', 'TradingPhaseCode', 'MDRecordType',
                      'HTSCSecurityID', 'ReceiveDateTime', 'MDValidType',
                      'TradingDate', 'PreOpenInterest', 'PreClosePx',
                      'PreSettlePrice', 'OpenPx', 'HighPx', 'LowPx', 'LastPx',
                      'TotalVolumeTrade', 'TotalValueTrade', 'TotalWeightTrade',
                      'OpenInterest', 'InitOpenInterest', 'InterestChg',
                      'ClosePx', 'SettlePrice', 'MaxPx', 'MinPx', 'AveragePx',
                      'LifeHighPx', 'LifeLowPx', 'BuyPx', 'BuyQty', 'BuyImplyQty',
                      'SellPx', 'SellQty', 'SellImplyQty',
                      'CommodityContractNumber', 'ExchangeDate', 'ExchangeTime',
                      'ArrivalDateTime', 'Buy1Price', 'Buy1OrderQty', 'Sell1Price',
                      'Sell1OrderQty', 'Buy2Price', 'Buy2OrderQty', 'Sell2Price',
                      'Sell2OrderQty', 'Buy3Price', 'Buy3OrderQty', 'Sell3Price',
                      'Sell3OrderQty', 'Buy4Price', 'Buy4OrderQty', 'Sell4Price',
                      'Sell4OrderQty', 'Buy5Price', 'Buy5OrderQty', 'Sell5Price',
                      'Sell5OrderQty', 'Buy6Price', 'Buy6OrderQty', 'Sell6Price',
                      'Sell6OrderQty', 'Buy7Price', 'Buy7OrderQty', 'Sell7Price',
                      'Sell7OrderQty', 'Buy8Price', 'Buy8OrderQty', 'Sell8Price',
                      'Sell8OrderQty', 'Buy9Price', 'Buy9OrderQty', 'Sell9Price',
                      'Sell9OrderQty', 'Buy10Price', 'Buy10OrderQty',
                      'Sell10Price', 'Sell10OrderQty']

    #含买卖盘的tick数据
    @staticmethod
    def getMDTickABAttrNames():
        attrnames = SecurityTypeName.MDTickAttrNames.copy()
        withnames = ["WeightedAvgBidPx","WeightedAvgOfferPx","TotalBidNumber","TotalOfferNumber"]
        attrnames.extend(withnames)
        for i in range(1,11):
            attrnames.append("Buy"+str(i)+"Price")
            attrnames.append("Buy"+str(i)+"OrderQty")
            attrnames.append("Sell"+str(i)+"Price")
            attrnames.append("Sell"+str(i)+"OrderQty")
        return attrnames

    @staticmethod
    def getMDTickFundAttrNames():
        attrnames = SecurityTypeName.MDFundAttNames.copy()
        withnames = ["WeightedAvgBidPx","WeightedAvgOfferPx","TotalBidNumber","TotalOfferNumber"]
        attrnames.extend(withnames)
        for i in range(1,11):
            attrnames.append("Buy"+str(i)+"Price")
            attrnames.append("Buy"+str(i)+"OrderQty")
            attrnames.append("Sell"+str(i)+"Price")
            attrnames.append("Sell"+str(i)+"OrderQty")
        return attrnames
    
    #期货tick数据
    MDTickFuturesAttrNames = ["MDDate","MDTime","SecurityType","TradingDate","PreOpenInterest","PreClosePx","PreSettlePrice","OpenPx",
                             "HighPx","LowPx","LastPx","TotalVolumeTrade","TotalValueTrade","OpenInterest","ClosePx","SettlePrice",
                             "PreDelta","CurrDelta","HTSCSecurityID"]
    
    #含买卖盘的期货tick数据
    @staticmethod
    def geMDTickABFuturesAttrNames():
        attrnames = SecurityTypeName.MDTickFuturesAttrNames.copy()
        withnames = ["WeightedAvgBidPx","WeightedAvgOfferPx","TotalBidNumber","TotalOfferNumber"]
        attrnames.extend(withnames)
        for i in range(1,6):
            attrnames.append("Buy"+str(i)+"Price")
            attrnames.append("Buy"+str(i)+"OrderQty")
            attrnames.append("Sell"+str(i)+"Price")
            attrnames.append("Sell"+str(i)+"OrderQty")
        return attrnames

    #期货tick数据
    MDTickOptionsAttrNames = ["MDDate","MDTime","SecurityType","TradingDate","PreOpenInterest","PreClosePx","PreSettlePrice","OpenPx",
                              "HighPx","LowPx","LastPx","TotalVolumeTrade","TotalValueTrade","OpenInterest","ClosePx","SettlePrice",
                              "PreDelta","CurrDelta","HTSCSecurityID"]
    #含买卖盘的期货tick数据
    @staticmethod
    def geMDTickABOptionsAttrNames():
        attrnames = SecurityTypeName.MDTickOptionsAttrNames.copy()
        withnames = ["WeightedAvgBidPx","WeightedAvgOfferPx","TotalBidNumber","TotalOfferNumber"]
        attrnames.extend(withnames)
        for i in range(1,6):
            attrnames.append("Buy"+str(i)+"Price")
            attrnames.append("Buy"+str(i)+"OrderQty")
            attrnames.append("Sell"+str(i)+"Price")
            attrnames.append("Sell"+str(i)+"OrderQty")
        return attrnames
    
    #K线
    MDKLineAttrNames = ["MDDate","MDTime","OpenPx","ClosePx","HighPx","LowPx","NumTrades","TotalVolumeTrade","TotalValueTrade",
                       "PeriodType","IOPV","OpenInterest","SettlePrice","HTSCSecurityID","KLineCategory"]
    
    #逐笔委托
    MDOrderAttrNames = ["MDDate","MDTime","OrderIndex","OrderType","OrderPrice","OrderQty","OrderBSFlag","HTSCSecurityID","ReceiveDateTime"]
    
    #委托队列
    MDOrderListAttrNames = ["MDDate","MDTime","TotalVolumeTrade","TotalValueTrade","HTSCSecurityID","Buy1NumOrders","Buy1NoOrders",
                           "Sell1NumOrders","Sell1NoOrders"]
    
    
    #实时股票数据
    #最新的股票tick数据
    RealTimeStockTickAttNames = ["HTSCSecurityID", "MDDate","MDTime", "TotalVolumeTrade", "TotalValueTrade", "LastPx", "OpenPx", "ClosePx","HighPx", "LowPx", "PreClosePx", "ReceiveDateTime"]

    #最新的指数tick数据
    RealTimeIndexTickAttNames = ["HTSCSecurityID","MDDate","MDTime", "TotalVolumeTrade","TotalValueTrade", "LastPx", "OpenPx", "ClosePx", "HighPx", "LowPx","PreClosePx","ReceiveDateTime"]