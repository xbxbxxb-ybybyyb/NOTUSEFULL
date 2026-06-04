from Utils_CV.InputManager import InputManager
from Utils_CV.ResultManager import ResultManager
from Utils_CV.ThreadingManager import ThreadingManager
import Utils_CV.HelperFunctions as hf
from analyze_result import analyze_result


"""
该版本适用于XQuant的Spark并行计算环境，进行参数遍历选取最优
**对于下面第9条，不必要的参数设为了np.nan，请在降低参数维度的过程中，使用np.nanmean, np.nanmax等方法

如果不明白参数的意义：
1. signal_csv_dir: 读取数据的路径，以SHARE_21作为参数开头！一般放置于HDFS的 共享文件夹->股票策略交易团队下，若无数据请联系011478和013050进行上传。
2. output_dir: 输出xls报告的根目录，以个人六位工号作为参数开头！具体输出时，会在目录下创建以股票代码为名字的文件夹，（固定名称的）报告则会在下一级生成。
3. executor_str: 执行的交易逻辑。具体写法请联系011478。默认为SignalExecutorTesting，与峰哥执行回测的交易逻辑完全一致，可作为benchmark。
4. symbols: 回测的股票列表，请确保signal_csv_dir中，含有股票列表的信号数据。支持单个股票。
5. init_quantities: 回测的初始股数，与symbols一一对应。如果长度不同，则会报错。支持单个股票。
6. open_triggers: （做多）开仓阈值参数遍历范围。支持单个参数及多个参数。
7. close_triggers: （做多）平仓阈值参数遍历范围。支持单个参数及多个参数。
8. cross_valid: 是否交叉验证。（具体做法请咨询013050）
9. param_reduction: 减少不必要的参数遍历。将过大的（做多）开仓阈值去除，以提高回测效率。（如果全部被剔除，则会报错，但不影响其他股票的回测）
10. max_tasks: 分配的计算资源/核心数，默认为200，团队最大使用数量200。

如果想要自定义方法：
1. 改变信号的均值求法: SignalManager -> def __pre_process_single
2. 改变回测的风控指标: InputManager -> def __init__ -> mock_trade_para
3. 改变param_reduction方法: InputManager -> def __my_param_reduction 请确保开平参数最终能输出一个矩阵

**4. 改变回测的方式: Please derive from SignalExecutorBase
**5. 改变阈值的评价方式: ResultManager -> def __my_best_param_solution 如果在评价时需要更多的评价指标，可以显示定义构造函数的default_keys

如果疑问请联系: 011478
"""
def bt_cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str='SignalExecutorTesting', 
     overwrite_params={}, max_tasks=400):
    
   
    open_triggers = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0]
    close_triggers = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    input_manager = InputManager(signal_csv_dir=signal_csv_dir, bt_dir=bt_dir, output_dir=output_dir, executor_str=executor_str, cross_valid=True)
    for key in overwrite_params.keys():
        input_manager.mock_trade_para.update({key: overwrite_params[key]})
    input_manager.set_symbols(symbols)
    input_manager.set_init_quantity(init_quantities)
    input_manager.set_triggers(open_triggers, close_triggers, param_reduction=True)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks)

    threading_manager.start()

    print('done')
    
def main():
    print('For 5160701Big...')
    max_tasks = 600
    portfolio = 'big'
    sdate_str = '20190415'
    edate_str = '20190621'
    executor_str = 'SignalExecutorTesting'
    # bt_dir = '666888/TEMP+3a58ac34-5b73-11e9-b681-e8611f1f6efe/20190211-20190412_20190413/5161101+800arb/'
    bt_dir = 'SHARE_21/ModelProduction/20190101_48_end/bt_info/{}-{}_20190626/{}/'.format(sdate_str, edate_str, portfolio)
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    # signal_csv_dir = 'SHARE_21/ModelProduction/20190101_end/signals/'
    signal_csv_dir = 'SHARE_21/ModelProduction/20190101_48_end/universe/'
    hdfs_root = '666888/production/'
    # result_dir_name = 'cv-{}-{}-{}-SOME-OTHER-USEFUL-HINTS/'.format(sdate_str, edate_str, portfolio)
    result_dir_name = 'cv-{}-{}_20190626-{}-200-800/'.format(sdate_str, edate_str, portfolio)
    output_dir = hdfs_root + result_dir_name
    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
    bt_cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, overwrite_params, max_tasks)
    analyze_result(portfolio, '{}-{}_20190626'.format(sdate_str, edate_str), hdfs_root, result_dir_name, bt_dir)
   
if "__main__" == __name__:
    main()
