from xquant.marketdata import MarketData
from HFDataLoader.Config import STOCK_RAW_ORDER_COLUMNS, STOCK_RAW_TRANSACTIONS_COLUMNS
from ExchangeHouse.MockTickData import MockTickData
import time

def get_order_data(code, trade_date):
    mdp = MarketData()
    df_data = mdp.get_data_by_time_frame("Order", code, str(trade_date) + " 091500000", str(trade_date) + " 150000250", ["1", "2", "3"])
    df_data = df_data[STOCK_RAW_ORDER_COLUMNS]
    return df_data

def get_transaction_data(code, trade_date):
    mdp = MarketData()
    df_data = mdp.get_data_by_time_frame("Transaction", code, str(trade_date) + " 091500000", str(trade_date) + " 150000250", ["1", "2", "3"])
    df_data = df_data[STOCK_RAW_TRANSACTIONS_COLUMNS]
    return df_data

if __name__=="__main__":
    stock = "000725.SZ"
    start_date = "20191202"
    end_date = "20191202"

    mtd = MockTickData(stock, 3)
    t1 = time.time()
    mock_tick_df, mock_tick_monitor = mtd.load_mock_tick_data(start_date, end_date)
    print("time cost: ", str(time.time()-t1))