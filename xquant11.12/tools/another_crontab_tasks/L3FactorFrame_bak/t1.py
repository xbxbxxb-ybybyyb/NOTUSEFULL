from L3FactorFrame.MarketDataManager import get_l3_trade_order_date
import polars as pl
tick_df, order_df, trade_df, cancel_df = get_l3_trade_order_date("688256.SH", "20240603")
with pl.Config(tbl_rows=-1):
    print(tick_df.head(30))