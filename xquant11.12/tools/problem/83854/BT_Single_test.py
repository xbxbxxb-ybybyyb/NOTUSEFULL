from Utils_BT.InputManager import InputManager
from Utils_BT.ResultManager import ResultManager
from Utils_BT.ThreadingManager import ThreadingManager
import Utils_BT.HelperFunctions as hf
from xquant.pyfile import Pyfile
import json
from analyze_result import analyze_result

"""
该版本适用于XQuant的Spark并行计算环境，进行指定（唯一）阈值的多个股票计算，得到回测报告
（报告为信号文件和阈值文件的交集股票，若缺少任一文件则会报错，该股票不会生成报告，但不会影响其他股票的正常运行）
（运行完请留意是否存在traceback)
本版本暂无优化计划，300只股票的预计完成时间为1min

如果不明白参数的意义：
1. signal_csv_dir: 读取数据的路径，以SHARE_21作为参数开头！一般放置于HDFS的 共享文件夹->股票策略交易团队下，若无数据请联系011478和013050进行上传。
2. output_dir: 输出xls报告的根目录，以个人六位工号作为参数开头！具体输出时，会在目录下创建以股票代码为名字的文件夹，（固定名称的）报告则会在下一级生成。
3. executor_str: 执行的交易逻辑。具体写法请联系011478。默认为SignalExecutorTesting，与峰哥执行回测的交易逻辑完全一致，可作为benchmark。
4. trigger_json_dir: 阈值参数目录。确保该目录下的阈值文件命名规则为: symbol + '.json'。
4. symbols: 回测的股票列表，请确保signal_csv_dir中，含有股票列表的信号数据。支持单个股票。
5. init_quantities: 回测的初始股数，与symbols一一对应。如果长度不同，则会报错。支持单个股票。
6. max_tasks: 分配的计算资源/核心数，默认为200，团队最大使用数量200。

如果想要自定义方法：
1. 改变信号的均值求法: SignalManager -> def __pre_process_single
2. 改变回测的风控指标: InputManager -> def __init__ -> mock_trade_para
3. 改变param_reduction方法: InputManager -> def __my_param_reduction 请确保开平参数最终能输出一个矩阵

**4. 改变回测的方式: Please derive from SignalExecutorBase
**5. 改变阈值的评价方式: ResultManager -> def __my_best_param_solution 如果在评价时需要更多的评价指标，可以显示定义构造函数的default_keys

如果疑问请联系: 011478
"""



def BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params={}, max_tasks=400):
    input_manager = InputManager(signal_csv_dir=signal_csv_dir, bt_dir=bt_dir, output_dir=output_dir, executor_str=executor_str, trigger_json_dir=trigger_json_dir)
    for key in overwrite_params.keys():
        input_manager.mock_trade_para.update({key: overwrite_params[key]})
    input_manager.set_symbols(symbols)
    input_manager.set_init_quantity(init_quantities)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks)

    threading_manager.start()

    print('done')

def main():
    
    sdate_str = '20181201'
    edate_str = '20190201'
    executor_str = 'SignalExecutorTesting'
    max_tasks = 400
    portfolio = '5161101'
    bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}_20190216/{}/'.format(sdate_str, edate_str, portfolio)
    # symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    symbols = ['000333.SZ']
    init_quantities = [103617]
    signal_csv_dir = 'SHARE_21/ModelProduction/20181001_end/signals/'
    py = Pyfile()
    trigger_json_dir = '666888/production_triggers_month/{}/'.format(portfolio)
    with py.open('production_triggers_month/{}/come_from.json'.format(portfolio), 'rb') as f:
        name = f.read()
        name = json.loads(name)
    hdfs_root = '666888/test/'
    result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(sdate_str, edate_str, portfolio, name)
    output_dir = hdfs_root + result_dir_name
    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
    BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)
    analyze_result(portfolio, '{}-{}_20190216'.format(sdate_str, edate_str), hdfs_root, result_dir_name, bt_dir)

if __name__ == '__main__':
    main()