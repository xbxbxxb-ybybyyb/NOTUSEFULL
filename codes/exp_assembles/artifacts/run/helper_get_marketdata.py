from MDCDataProvider.MDCDataProvider import MDCDataProvider
import sys
mdc = MDCDataProvider()

stock = sys.argv[1]
start_date = sys.argv[2]
end_date = sys.argv[3]
save_file_name = sys.argv[4]

daily_market_df = mdc.get_data_by_time_frame("StockTick", stock, "{} 093000000".format(start_date),
                                             "{} 150000000".format(end_date))
daily_market_df.to_parquet(f"{save_file_name}")