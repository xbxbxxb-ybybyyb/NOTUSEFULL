from xquant.marketdata import MarketData
mdp = MarketData()
import pandas as pd
import datetime as dt
import time
import random
import ray


@ray.remote
def test(stock, date, is_save=False):
#     stock = list(stock)
    # is_save_cdp：是否存储数据到吉山库，is_save_cdh5：是否存储数据到奥体库
    # TODO 因子计算及存储逻辑
    start = time.time()
    price_data1 = mdp.get_data_by_date("Stock", stock, date)
    price_data2 = mdp.get_data_by_date("Transaction", stock, date)
    price_data3 = mdp.get_data_by_date("Order", stock, date)
#     print("++++++++++++++++{}+++++++++++++++".format(time.time()-start))
#     price_data1 = DataSource('level2_snapshot_CN_STOCK_A').read(instruments=stock, start_date=date, end_date=date)
#     price_data2 = DataSource('level2_trade_CN_STOCK_A').read(instruments=stock, start_date=date, end_date=date)
#     price_data3 = DataSource('level2_order_CN_STOCK_A').read(instruments=stock, start_date=date, end_date=date)
#     print("++++++++++++++++get_data+++++++++++++++")
    mtime_range1 = pd.date_range('2002/5/6 09:30:00', '2002/5/6 11:30:00', freq='s').tolist()
    mtime_range2 = pd.date_range('2002/5/6 13:00:00', '2002/5/6 15:00:00', freq='s').tolist()
#     上午下午各7201条数据，各取前6000条
    mtime_range = mtime_range1[:6000] + mtime_range2[:6000]
 
    # 循环计算因子的次数，共400个因子
    n = 400
    df_list = []
    fac_list = []
    for j in range(0, n, 4):
        # 因子1
        if price_data1.empty:
            pass
        else:
            n_tick = 6
            fac_name1 = 'fac_' + str(j + 1)
            fac1 = pd.DataFrame()
#             price_data1['MDTime'] = price_data1['date'].apply(lambda x:x.strftime("%H%M%S%f")[:-3])
            price_data1['MDTime'] = price_data1['MDTime'].apply(lambda x: x[:6])
            fac1[fac_name1] = price_data1['LastPx'].groupby(price_data1['MDTime']).mean()
            fac1.reset_index(inplace=True)
            fac1['MDTime'] = fac1['MDTime'].apply(lambda x: x + '000')
            fac1.set_index('MDTime', inplace=True)
            fac1[fac_name1] = fac1[fac_name1] / fac1[fac_name1].shift(n_tick) * 1000
            df_list.append(fac1)
            fac_list.append(fac_name1)
 
        # 因子2
        if price_data2.empty:
            pass
        else:
            fac_name2 = 'fac_' + str(j + 2)
            fac2 = pd.DataFrame()
#             price_data2['MDTime'] = price_data2['date'].apply(lambda x:x.strftime("%H%M%S%f")[:-3])
            price_data2['MDTime'] = price_data2['MDTime'].apply(lambda x: x[:6])
            fac2[fac_name2] = price_data2['TradePrice'].groupby(price_data2['MDTime']).mean()
            fac2.reset_index(inplace=True)
            fac2['MDTime'] = fac2['MDTime'].apply(lambda x: x + '000')
            fac2.set_index('MDTime', inplace=True)
            fac2[fac_name2] = fac2[fac_name2].skew()
            df_list.append(fac2)
            fac_list.append(fac_name2)
 
        # 因子3
        if price_data3.empty:
            pass
        else:
            fac_name3 = 'fac_' + str(j + 3)
            fac3 = pd.DataFrame()
#             price_data3['MDTime'] = price_data3['date'].apply(lambda x:x.strftime("%H%M%S%f")[:-3])
            price_data3['MDTime'] = price_data3['MDTime'].apply(lambda x: x[:6])
            fac3[fac_name3] = price_data3['OrderPrice'].groupby(price_data3['MDTime']).mean()
            fac3.reset_index(inplace=True)
            fac3['MDTime'] = fac3['MDTime'].apply(lambda x: x + '000')
            fac3.set_index('MDTime', inplace=True)
            std_ts = fac3.std(axis=1, ddof=0)
            std_ts.loc[std_ts == 0] = 1
            fac3 = fac3.divide(std_ts, axis=0)
            df_list.append(fac3)
            fac_list.append(fac_name3)
 
        # 造数存储
        fac_name4 = 'fac_' + str(j + 4)
        row_num = 12000
        data_list = []
        # lst_num：值为列表的因子个数
        lst_num = 10
        if int(j / 4) < lst_num:
            for i in range(row_num):
                data_list.append([mtime_range[i], str([round(random.uniform(10, 100), 2)] * 10)])
                i += 1
        else:
            for i in range(row_num):
                data_list.append([mtime_range[i], round(random.uniform(10, 100), 2)])
                i += 1
        fac4 = pd.DataFrame(data_list, columns=['MDTime', fac_name4])
        # %f为微秒级，与行情数据MDTime保持一致取前九位到毫秒级
        fac4['MDTime'] = fac4['MDTime'].apply(lambda x: dt.datetime.strftime(x, '%H%M%S%f')[:9])
        fac4.set_index('MDTime', inplace=True)
        df_list.append(fac4)
        fac_list.append(fac_name4)
 
 
#     if df_list:
#         df = pd.concat(df_list, axis=1)
    if is_save:
         
        return
    return
if __name__ == "__main__":
    stock_list = pd.read_pickle("/data/user/013150/StockList.pkl")[:10]
    # import ray
    ray.shutdown()
    ray.init()
    start = time.time()
    remainings = [test.remote(stock, date='20211108', is_save=False) for stock in stock_list]
    done = 0
    ready_list = []
    while remainings:
        ready, remainings = ray.wait(remainings)
        ready_list += ready
        done += len(ready)
        if done % 1 == 0:
            print(time.time()-start, done/(len(remainings)+done))
        
