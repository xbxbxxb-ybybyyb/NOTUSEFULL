"""
Handles the output in SignalEvaluate
Use "register" when an order is finished
Get the info you want, then output the results

by 011478
"""
import datetime as dt
import pandas as pd
from typing import Dict, Tuple
from xquant.pyfile import Pyfile


class OutputManager:
    def __init__(self, symbol, target_qty, target_value, vwap_df):
        self.__symbol = symbol
        self.__target_qty = target_qty
        self.__target_value = target_value
        self.__orders = {}  # dict of detailed orders: key = columns, value = values 多一个OrderTimeDT(dt.datetime)
        self.__columns = ["No", "Code", "Date", "OrderTime", "Side", "Price", "EmaVolume", "QuoteVolume", "Quantity",
                          "CumQty", "OrderAmount", "CumAmount", "AvgPrice", "MarketVWAP", "StrategyVWAP", "Status",
                          "SignalType", "Duration"]
        self.__init_orders()
        self.__vwap_df = vwap_df

        self.__dates = set()
        self.__side_dict = {"B": "long", "S": "short"}

    def __init_orders(self):
        for key in self.__columns:
            self.__orders.update({key: []})
        self.__orders.update({"OrderTimeDT": []})

    def onNewDay(self, date: dt.datetime.date):
        self.__dates.add(dt.datetime(date.year, date.month, date.day).strftime("%Y-%m-%d"))

    def register(self, order):
        self.__orders["No"].append(order.order_number)
        self.__orders["Code"].append(order.code)
        self.__orders["Date"].append(dt.datetime.fromtimestamp(order.order_time).strftime("%Y-%m-%d"))
        self.__orders["OrderTime"].append(dt.datetime.fromtimestamp(order.order_time).strftime("%H:%M:%S"))
        self.__orders["Side"].append(self.__side_dict[order.direction])
        self.__orders["Price"].append(order.price)
        self.__orders["Quantity"].append(order.volume)
        self.__orders["CumQty"].append(order.volume_executed)
        self.__orders["OrderAmount"].append(order.price * order.volume)
        self.__orders["CumAmount"].append(order.amount_executed)
        self.__orders["AvgPrice"].append(order.amount_executed / order.volume_executed
                                         if order.volume_executed > 0 else 0)
        self.__orders["Status"].append(order.order_status)
        self.__orders["SignalType"].append(order.signal_type.name)
        self.__orders["Duration"].append(order.duration)
        self.__orders["MarketVWAP"].append(order.market_vwap)
        self.__orders["StrategyVWAP"].append(order.strategy_vwap)
        self.__orders["EmaVolume"].append(order.ema_volume)
        self.__orders["QuoteVolume"].append(order.quote_volume)
        self.__orders["OrderTimeDT"].append(dt.datetime.fromtimestamp(order.order_time))  # hidden

    def get_detailed_orders_df(self):
        # Sheet: orders
        orders_df = pd.DataFrame(data=self.__orders, columns=self.__columns)

        if orders_df.loc[0, "MarketVWAP"] is None or orders_df.loc[0, "StrategyVWAP"] is None:
            orders_df = orders_df.drop(columns=["MarketVWAP", "StrategyVWAP"])
        else:
            orders_df["PriceDeviation"] = (orders_df["StrategyVWAP"] / orders_df["MarketVWAP"] - 1).abs()

        if orders_df.loc[0, "EmaVolume"] is None or orders_df.loc[0, "QuoteVolume"] is None:
            orders_df = orders_df.drop(columns=["EmaVolume", "QuoteVolume"])

        return orders_df

    def stat(self):
        if len(self.__orders["No"]) == 0:
            raise Exception("No orders for {}".format(self.__symbol))
        
        # Sheet: daily
        dates_str = list(self.__dates)
        dates_str.sort()
        daily_df = pd.DataFrame(
            0,
            index=dates_str,
            columns=["Amount", "Quantity", "Traded", "VWAP", "FinishedRate", "AvgDuration", "CancelledRatio",
                     "QuantityCompletionRatio", "TotalOrderNum", "AggressiveNum", "PassiveNum", "IntervalEndNum",
                     "MarketCloseMorningNum", "MarketCloseNum", "PriceDeviationNum", "LowVolatilityNum",
                     "InvalidSignalNum", "PriceLimitNum", "PriceLimitOpenNum"]
        )

        for i in range(len(self.__orders.get("No", []))):
            date = self.__orders["OrderTimeDT"][i].strftime("%Y-%m-%d")
            daily_df.loc[date, "Amount"] += self.__orders["CumAmount"][i]
            daily_df.loc[date, "Quantity"] += self.__orders["CumQty"][i]
            daily_df.loc[date, "FinishedRate"] = daily_df.loc[date, "Quantity"] / abs(self.__target_qty)
            daily_df.loc[date, "Traded"] = 1  # 是否发生交易

            if self.__orders["SignalType"][i] == "aggressive":
                daily_df.loc[date, "AggressiveNum"] += 1
            elif self.__orders["SignalType"][i] == "passive":
                daily_df.loc[date, "PassiveNum"] += 1
            elif self.__orders["SignalType"][i] == "invalid_signal":
                daily_df.loc[date, "InvalidSignalNum"] += 1
            elif self.__orders["SignalType"][i] == "interval_end":
                daily_df.loc[date, "IntervalEndNum"] += 1
            elif self.__orders["SignalType"][i] == "market_close":
                daily_df.loc[date, "MarketCloseNum"] += 1
            elif self.__orders["SignalType"][i] == "price_limit":
                daily_df.loc[date, "PriceLimitNum"] += 1
            elif self.__orders["SignalType"][i] == "price_limit_open":
                daily_df.loc[date, "PriceLimitOpenNum"] += 1
            elif self.__orders["SignalType"][i] == "price_deviation":
                daily_df.loc[date, "PriceDeviationNum"] += 1
            elif self.__orders["SignalType"][i] == "low_volatility":
                daily_df.loc[date, "LowVolatilityNum"] += 1
            elif self.__orders["SignalType"][i] == "market_close_morning":
                daily_df.loc[date, "MarketCloseMorningNum"] += 1
            daily_df.loc[date, "TotalOrderNum"] += 1

            daily_df.loc[date, "AvgDuration"] += self.__orders["Duration"][i]

            if self.__orders["Status"][i] == "cancelled":
                daily_df.loc[date, "CancelledRatio"] += 1

            daily_df.loc[date, "QuantityCompletionRatio"] += self.__orders["Quantity"][i]

        daily_df["Cost"] = daily_df["Amount"] / daily_df["Quantity"]
        daily_df["AvgDuration"] /= daily_df["TotalOrderNum"]
        daily_df["CancelledRatio"] /= daily_df["TotalOrderNum"]
        daily_df["QuantityCompletionRatio"] = daily_df["Quantity"] / daily_df["QuantityCompletionRatio"]

        order_side = self.__orders["Side"][0]

        # VWAP
        buy_vwap_df, sell_vwap_df = self.__vwap_df
        dates_int = map(lambda x: int(x[:4] + x[5:7] + x[8:10]), dates_str)
        if order_side == "long":
            for date_str, date_int in zip(dates_str, dates_int):
                daily_df.loc[date_str, "VWAP"] = buy_vwap_df.loc[date_int, self.__symbol]
        else:
            for date_str, date_int in zip(dates_str, dates_int):
                daily_df.loc[date_str, "VWAP"] = sell_vwap_df.loc[date_int, self.__symbol]

        # 战胜幅度
        # 汇总金额
        if order_side == "long":
            daily_df["WRatio"] = (daily_df["VWAP"] - daily_df["Cost"]) / daily_df["VWAP"]
            daily_df["Saved"] = (daily_df["VWAP"] - daily_df["Cost"]) * daily_df["Quantity"]
        else:
            daily_df["WRatio"] = (daily_df["Cost"] - daily_df["VWAP"]) / daily_df["VWAP"]
            daily_df["Saved"] = (daily_df["Cost"] - daily_df["VWAP"]) * daily_df["Quantity"]
        daily_df = daily_df.fillna(0)

        # Sheet: summary
        summary_df = pd.DataFrame(index=[0])
        summary_df["Symbol"] = self.__symbol
        summary_df["TargetQty"] = self.__target_qty
        summary_df["TargetMV"] = self.__target_value
        summary_df["DayCounts"] = daily_df["Traded"].sum()
        summary_df["WinCounts"] = (daily_df["WRatio"] > 0).sum()
        summary_df["WinRate"] = summary_df.loc[0, "WinCounts"] / summary_df.loc[0, "DayCounts"]

        WVWAP = (daily_df["VWAP"] * daily_df["Quantity"]).sum() / daily_df["Quantity"].sum()
        WCost = (daily_df["Cost"] * daily_df["Quantity"]).sum() / daily_df["Quantity"].sum()
        if order_side == "long":
            WRatio = (WVWAP - WCost) / WVWAP
        else:
            WRatio = (WCost - WVWAP) / WVWAP

        summary_df["WVWAP"] = WVWAP
        summary_df["WCost"] = WCost
        summary_df["WRatio"] = WRatio
        summary_df["TotalSaved"] = daily_df["Saved"].sum()
        summary_df["AvgFinishedRate"] = daily_df["FinishedRate"].mean()
        summary_df["AvgDuration"] = daily_df["AvgDuration"].mean()
        summary_df["AvgCancelledRatio"] = daily_df["CancelledRatio"].mean()
        summary_df["AvgQuantityCompletionRatio"] = daily_df["QuantityCompletionRatio"].mean()
        summary_df["AvgTotalOrderNum"] = daily_df["TotalOrderNum"].mean()
        summary_df["AggressivePercentage"] = daily_df["AggressiveNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["PassivePercentage"] = daily_df["PassiveNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["IntervalEndPercentage"] = daily_df["IntervalEndNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["MarketCloseMorningPercentage"] = (daily_df["MarketCloseMorningNum"].sum()
                                                      / daily_df["TotalOrderNum"].sum())
        summary_df["MarketClosePercentage"] = daily_df["MarketCloseNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["PriceDeviationPercentage"] = daily_df["PriceDeviationNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["LowVolatilityPercentage"] = daily_df["LowVolatilityNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["InvalidSignalPercentage"] = daily_df["InvalidSignalNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["PriceLimitPercentage"] = daily_df["PriceLimitNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df["PriceLimitOpenPercentage"] = daily_df["PriceLimitOpenNum"].sum() / daily_df["TotalOrderNum"].sum()
        summary_df = summary_df.fillna(0)

        # return
        daily_df.index.name = "Date"
        daily_df = daily_df[["Amount", "Quantity", "VWAP", "Cost", "WRatio", "Saved", "FinishedRate", "AvgDuration",
                             "CancelledRatio", "QuantityCompletionRatio", "TotalOrderNum", "AggressiveNum",
                             "PassiveNum", "IntervalEndNum", "MarketCloseMorningNum", "MarketCloseNum",
                             "PriceDeviationNum", "LowVolatilityNum", "InvalidSignalNum", "PriceLimitNum",
                             "PriceLimitOpenNum"]]

        return daily_df, summary_df

    def to_excel(self, path, trigger: Dict[str, float], stats: Tuple[pd.DataFrame, pd.DataFrame] = None):
        orders_df = self.get_detailed_orders_df()
        if stats is None:
            daily_df, summary_df = self.stat()
        else:
            daily_df, summary_df = stats
        summary_df.loc[0, "longAggressiveRatio"] = trigger["longAggressiveRatio"]
        summary_df.loc[0, "longPassiveRatio"] = trigger["longPassiveRatio"]
        summary_df.loc[0, "shortAggressiveRatio"] = trigger["shortAggressiveRatio"]
        summary_df.loc[0, "shortPassiveRatio"] = trigger["shortPassiveRatio"]
        py = Pyfile()
        if py.exists(path):
            py.delete(path)
        with py.open(path, "wb") as f:
            writer = pd.ExcelWriter(f, engine="xlsxwriter")
            orders_df.to_excel(writer, sheet_name="orders", index=False)
            daily_df.to_excel(writer, sheet_name="daily")
            summary_df.to_excel(writer, sheet_name="summary", index=False)
            writer.save()
