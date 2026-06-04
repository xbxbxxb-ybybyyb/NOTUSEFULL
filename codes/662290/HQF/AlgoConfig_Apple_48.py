import time
import DataAPI.DataToolkit as Dtk
today = int(time.strftime('%Y%m%d'))

#today = 20200918
##############################################
start_date = today
end_date = today
save_path = '/data/user/015618/HQF_Daily/'
PanelMinData_path = '/data/user/015618/HQF_Monthly/'
PanelMinData_path = "/data/group/800080/PanelMinDataForZT/stock/"
##############################################

start_date_pre = Dtk.get_n_days_off(start_date,-2)[0]



config = {
    "outputDir": "output",
    "StrategyName": "AlgoShaolin",
    "LibraryName": "HQF",
    "TagNames": ["timestamp", "tag1minLong", "tag1minShort", "tag2minLong", "tag2minShort",
                 "tag5minLong", "tag5minShort", "tag10minLong", "tag10minShort"],
    "UseConfigTradingUnderlyingCode": "false",
    "TradingUnderlyingCode": [["000001.SZ"]],
    "FactorUnderlyingCode": [],
    "StartDateTime": int('{}093015'.format(start_date_pre)),
    "EndDateTime": int('{}145659'.format(end_date)),
    "FactorSet": [
        {"name": "factorAccAmountBuy", "className": "FactorAccAmountBuy", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorAccAmountSell", "className": "FactorAccAmountSell", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyOrderAmt", "className": "FactorBuyOrderAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyOrderVol", "className": "FactorBuyOrderVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellOrderAmt", "className": "FactorSellOrderAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellOrderVol", "className": "FactorSellOrderVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorActiveBuyOrderAmt", "className": "FactorActiveBuyOrderAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorActiveBuyOrderVol", "className": "FactorActiveBuyOrderVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorPassiveBuyOrderAmt", "className": "FactorPassiveBuyOrderAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorPassiveBuyOrderVol", "className": "FactorPassiveBuyOrderVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorActiveSellOrderAmt", "className": "FactorActiveSellOrderAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorActiveSellOrderVol", "className": "FactorActiveSellOrderVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorPassiveSellOrderAmt", "className": "FactorPassiveSellOrderAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorPassiveSellOrderVol", "className": "FactorPassiveSellOrderVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyOrderCanceledAmt", "className": "FactorBuyOrderCanceledAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyOrderCanceledVol", "className": "FactorBuyOrderCanceledVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellOrderCanceledAmt", "className": "FactorSellOrderCanceledAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellOrderCanceledVol", "className": "FactorSellOrderCanceledVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorTradeNum", "className": "FactorTradeNum", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyTradeNum", "className": "FactorBuyTradeNum", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyTradeAmt", "className": "FactorBuyTradeAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorBuyTradeVol", "className": "FactorBuyTradeVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellTradeNum", "className": "FactorSellTradeNum", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellTradeAmt", "className": "FactorSellTradeAmt", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"},

        {"name": "factorSellTradeVol", "className": "FactorSellTradeVol", "indexTradingUnderlying": [0],
         "indexFactorUnderlying": [], "save": "True"}
    ],

    "Tag": {"indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraMaxDropHorizon": 0.002,
            "paraEmaMidPriceLag": 4, "paraOrderPressureLag": 4, "paraNumOrderMax": 5, "paraNumOrderMin": 1,
            "paraEmaSlicePressureLag": 8, "paraMaxLose": 0.004, "paraFastLag": 10, "paraSlowLag": 20}

}
