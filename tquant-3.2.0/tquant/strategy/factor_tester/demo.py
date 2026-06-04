import tquant.strategy.factor_tester.tester_analysis as Tester
from tquant import StockData

sd = StockData()


def factor_tester(start_date='20190102', end_date='20191231'):
    excess_return_path = '/app/mount/factor_return/'
    freq = 'DAY'
    factor_name = 'barra_cne6_beta'
    stock_list = sd.get_plate_info('MARKET', end_date, 'ALLA')['stock'].tolist()
    factor_data = sd.get_factor_barrarisk6(stock_list, (start_date, end_date), [factor_name])
    factor_result = {}
    factor_result[factor_name] = factor_data
    if freq == 'DAY':
        test_result, statu = Tester.test(start_date, end_date, factor_result=factor_result,
                                         excess_return_path=excess_return_path)
        print("test_result: ", test_result, statu)
    else:
        test_result = False


if __name__ == "__main__":
    factor_tester()
