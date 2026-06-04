from xquant.factordata import FactorData

fd = FactorData()

factor_names = [
    "timestamp",
    "factorAccAmountBuy",
    "factorAccAmountSell",
    "factorBuyOrderAmt",
    "factorBuyOrderVol",
    "factorSellOrderAmt",
    "factorSellOrderVol",
    "factorActiveBuyOrderAmt",
    "factorActiveBuyOrderVol",
    "factorPassiveBuyOrderAmt",
    "factorPassiveBuyOrderVol",
    "factorActiveSellOrderAmt",
    "factorActiveSellOrderVol",
    "factorPassiveSellOrderAmt",
    "factorPassiveSellOrderVol",
    "factorBuyOrderCanceledAmt",
    "factorBuyOrderCanceledVol",
    "factorSellOrderCanceledAmt",
    "factorSellOrderCanceledVol",
    "factorTradeNum",
    "factorBuyTradeNum",
    "factorBuyTradeAmt",
    "factorBuyTradeVol",
    "factorSellTradeNum",
    "factorSellTradeAmt",
    "factorSellTradeVol"
]


factor_df = fd.get_factor_value("GaoPinMiaoShuXingYinZi2", "000001.SZ", "20190506", factor_names)
print(factor_df)