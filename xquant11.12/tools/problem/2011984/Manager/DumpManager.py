import copy
import datetime
import pickle
import numpy as np
import pandas as pd
from Utils.UtilsTime import minute_t2m, minute_m2t
from xquant.xqutils.xqfile import HDFSFile
from xquant.factordata import FactorData


DetailedOrdersTitleNames = ['tradeNo', 'code', 'freq', 'orderTime', 'direction', 'price', 'quantity', 'avgPrice', 'cumQty',
                           'status', 'orderAmount', 'cumAmount']
ResultOrdersTitleNames = ['code', 'date', 'startTime', 'endTime', 'holdTime', 'direction', 'startPrice', 'endPrice',
                         'orderAmount', 'cumAmount', 'returnRate', 'afterCostProfit']
DateTitleNames = ['日期', '总市值', '总盈利', '交易次数', '获利次数', '胜率', '平均收益率', '利用率',
                 '交易总市值', '市值收益率', '获利收益率', '亏损收益率', '盈亏比',
                 '最大单笔亏损', '平均持仓时间', '撤单比']
SummaryPopTitleNames = ['date', 'order', 'preCostDailyProfit', 'afterCostDailyProfit', 'dailyOpenAmount', 'dailyCancelledRatio']


def concat_detail_orders(detailed_order_df):
    order_time_list = sorted(set(detailed_order_df["orderTime"].tolist()))
    order_df_list = []
    for order_time in order_time_list:
        order_d = detailed_order_df[detailed_order_df["orderTime"] == order_time]
        if order_d.shape[0] == 1:
            order_df_list.append(order_d)
        else:
            new_order_d = order_d.iloc[-1:]
            new_order_d[["quantity", "cumQty", "orderAmount", "cumAmount"]] = order_d[
                ["quantity", "cumQty", "orderAmount", "cumAmount"]].sum(axis=0).values
            order_df_list.append(new_order_d)
    new_order_df = pd.concat(order_df_list, axis=0)

    return new_order_df


class DumpManager(object):
    def __init__(self, symbol, dirPath, result, detailedOrders):
        self.symbol = symbol
        self.dirPath = dirPath
        self.result = result
        self.detailedOrders = detailedOrders

        self.fa = FactorData()
        self.hf = HDFSFile()

        self.dump_result_dict = dict()

    def run(self):
        """"""
        # DetailedOrders
        self.update_detailed_orders()

        # ResultOrders
        self.update_result_orders()

        # DateResult
        self.update_daily_result()

        # Summary
        self.update_summary()

        if self.hf.exists(self.dirPath):
            self.hf.delete(self.dirPath)

        with self.hf.open(self.dirPath, 'wb') as f:
            pickle.dump(self.dump_result_dict, f)

    def update_detailed_orders(self):
        """"""
        detailed_order_list = []
        for ir, orderList in enumerate(self.detailedOrders):
            for order in orderList:
                order_df = pd.Series(order).to_frame().T
                order_df["tradeNo"] = ir + 1
                order_df = order_df.reindex(columns=DetailedOrdersTitleNames)
                detailed_order_list.append(order_df)
        if len(detailed_order_list) > 0:
            detailed_order_df = pd.concat(detailed_order_list, axis=0)
            position = detailed_order_df["direction"].apply(lambda x: 1 if x == "long " else -1) * detailed_order_df["cumQty"]
            detailed_order_df["NetPosition"] = position.cumsum()
            detailed_order_df = detailed_order_df.reindex(columns=DetailedOrdersTitleNames + ["NetPosition"])
            detailed_order_df = concat_detail_orders(detailed_order_df)
        else:
            detailed_order_df = pd.DataFrame(columns=DetailedOrdersTitleNames + ["NetPosition"])

        self.dump_result_dict.update({"detailedOrders": detailed_order_df})

    def update_result_orders(self):
        """"""
        orders = self.result.get("order")
        orders_data_list = []
        for i in range(len(orders)):
            startTime = datetime.datetime.strptime(orders[i].get('startTime'), '%m/%d/%Y-%H:%M:%S:%f')
            endTime = datetime.datetime.strptime(orders[i].get('endTime'), '%m/%d/%Y-%H:%M:%S:%f')
            date = str(startTime).split(" ")[0]
            orders_data_daily = [orders[i].get('code'), date, str(startTime).split(" ")[1], str(endTime).split(" ")[1],
                                 str(endTime - startTime), orders[i].get('direction'), orders[i].get('startPrice'),
                                 orders[i].get('endPrice'), orders[i].get('orderAmount'), orders[i].get('cumAmount'),
                                 orders[i].get('returnRate') - 0.0012, orders[i].get('afterCostProfit')]
            orders_data_list.append(orders_data_daily)
        if len(orders_data_list) > 0:
            orders_data_df = pd.DataFrame(orders_data_list)
            orders_data_df.columns = ResultOrdersTitleNames
        else:
            orders_data_df = pd.DataFrame(columns=ResultOrdersTitleNames)

        self.dump_result_dict.update({"orders": orders_data_df})

    def update_daily_result(self):
        """"""
        init_qty = self.result['initQty']
        orders_data = self.dump_result_dict.get("orders")

        if orders_data.empty:
            daily_info_df = pd.DataFrame(columns=DateTitleNames)
        else:
            date_list = sorted(np.unique(orders_data["date"]))

            close_prices = self.fa.get_factor_value("Basic_factor", [self.symbol],
                                               list(map(lambda x: "".join(x.split("-")), date_list)), ["close"])
            market_value = (init_qty * close_prices["close"]).tolist()

            daily_info_list = []

            for i in range(len(date_list)):
                date = date_list[i]
                daily_data = orders_data[orders_data["date"] == date]

                afterCostProfit = sum(daily_data["afterCostProfit"])
                triggerTimes = daily_data.shape[0]
                winTimes = sum(daily_data["afterCostProfit"] > 0)
                winRate = winTimes / triggerTimes
                dailyOpenAmount = sum(daily_data["cumAmount"])

                afterCostProfit_earn = sum(daily_data[daily_data["afterCostProfit"] > 0]["afterCostProfit"])
                afterCostProfit_loss = sum(daily_data[daily_data["afterCostProfit"] < 0]["afterCostProfit"])
                dailyOpenAmount_earn = sum(daily_data[daily_data["afterCostProfit"] > 0]["cumAmount"])
                dailyOpenAmount_loss = sum(daily_data[daily_data["afterCostProfit"] < 0]["cumAmount"])
                earnReturnRate = afterCostProfit_earn / dailyOpenAmount_earn if dailyOpenAmount_earn != 0 else 0
                lossReturnRate = afterCostProfit_loss / dailyOpenAmount_loss if dailyOpenAmount_loss != 0 else 0
                EarnLossRate = round(-afterCostProfit_earn / afterCostProfit_loss, 2) if afterCostProfit_loss != 0 else "nan"

                holdTime = list(daily_data["holdTime"])
                for m in range(len(holdTime)):
                    holdTime[m] = minute_t2m(holdTime[m])
                aveHoldTime = np.mean(holdTime)
                aveHoldTime = minute_m2t(aveHoldTime)

                daily_info = [date, market_value[i], afterCostProfit, triggerTimes, winTimes,
                                  str(int(winRate * 100)) + "%",
                                  round(afterCostProfit / dailyOpenAmount * 1000, 2),
                                  str(int(dailyOpenAmount / market_value[i] * 100)) + "%", dailyOpenAmount,
                                  round(afterCostProfit / market_value[i] * 1000, 2),
                                  round(earnReturnRate * 1000, 2), round(lossReturnRate * 1000, 2), EarnLossRate,
                                  round(min(0, min(daily_data["returnRate"])) * 1000, 2), aveHoldTime,
                                  self.result['dailyCancelledRatio'][date]]

                daily_info_list.append(daily_info)

            if len(daily_info_list) > 0:
                daily_info_df = pd.DataFrame(daily_info_list, columns=DateTitleNames)
            else:
                daily_info_df = pd.DataFrame(columns=DateTitleNames)

        self.dump_result_dict.update({"dailyInfo": daily_info_df})

    def update_summary(self):
        """"""
        temp_result = copy.deepcopy(self.result)
        for name in SummaryPopTitleNames:
            temp_result.pop(name, None)

        summary_df = pd.Series(temp_result).to_frame().T
        summary_df = summary_df.reindex(columns=sorted(summary_df.columns.tolist()))

        self.dump_result_dict.update({"summary": summary_df})







