# -*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/26 15:53
INF_PREFIX = "INF"

INF_NONFACTOR_VALUE_COLUMNS = [
    "LastPrice",
    "LastPriceEw",
    "Volume",
    "Amount",
    "LastPriceRatioWeighted_5",
    "LastPriceTsRankMean_20",
    "MidPriceReturnsSkew_600",
    "TransBidVolumeRatio",
]

INF_NONFACTOR_ARRAY_COLUMNS = [
    "AskDelegateVolumeRatio",
    "BidDelegateVolumeRatio",
    "MidPriceReturnsRank_900",
    "MidPriceReturnsRank_300",
    "TransAskVolumeRank",
    "TransBidVolumeRank",
]

INF_NONFACTOR_COLUMNS = INF_NONFACTOR_VALUE_COLUMNS + INF_NONFACTOR_ARRAY_COLUMNS