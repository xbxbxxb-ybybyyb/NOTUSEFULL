from xquant.factordata import FactorData


def createLibrary(libraryName, factorList):
    fd = FactorData()

    try:
        fd.create_factor_library(libraryName, "T+0")
    except Exception as e:
        print(e)

    for factor in factorList:
        try:
            fd.add_factor(libraryName, [factor])
        except Exception as e:
            print(e)


if __name__ == "__main__":
    from HFDataLoader.Config import DAILY_STOCK_HBASE_COLUMNS, MINUTE_STOCK_HBASE_COLUMNS, TICK_STOCK_HBASE_COLUMNS
    from HFDataLoader.Config import MOCK_TICK_STOCK_HBASE_COLUMNS
    from HFDataLoader.Config import DAILY_INDEX_HBASE_COLUMNS, MINUTE_INDEX_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
    from HFDataLoader.Config import DAILY_MONITOR_HBASE_COLUMNS, MINUTE_MONITOR_HBASE_COLUMNS, TICK_MONITOR_HBASE_COLUMNS
    from HFDataLoader.Config import MOCK_TICK_MONITOR_HBASE_COLUMNS
    from HFDataLoader.Config import DAILY_CBOND_HBASE_COLUMNS
    from HFDataLoader.Config import DAILY_FUTURE_HBASE_COLUMNS, MINUTE_FUTURE_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS

    marketDataLibrary = "FutureDataLib"
    factorNames = list(set(DAILY_MONITOR_HBASE_COLUMNS + MINUTE_MONITOR_HBASE_COLUMNS + TICK_MONITOR_HBASE_COLUMNS +
                           MOCK_TICK_MONITOR_HBASE_COLUMNS +
                           DAILY_FUTURE_HBASE_COLUMNS + MINUTE_FUTURE_HBASE_COLUMNS + TICK_FUTURE_HBASE_COLUMNS ))
    createLibrary(marketDataLibrary, factorNames)
