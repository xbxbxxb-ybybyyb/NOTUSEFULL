import sys
sys.path.append("./")
import Utils.HelperFunctions as hf
from BT.bt_single import bt_single
from Analyzer.analyze_result import analyze_result
from xquant.factordata import FactorData
from xquant.pyfile import Pyfile


#py = Pyfile()
fd = FactorData()
mode = "multiprocessing"  # spark, local, multiprocessing
#mode = "local"


def main():
    print("Start Run BT Big")
    st_date = "20200601"
    ed_date = "20200831"
    dir_name = "bt_test"
    portfolio = "WuKong"
    executor_str = 'ProductionExecutor'
    result_dir_name = 'bt-{}-{}-{}-{}-3/'.format(st_date, ed_date, portfolio, executor_str)
    """
    ProductionExecutor2：原始结果（431w，benchmark）
    ProductionExecutorSP：当前实盘的Executor（410w）
    ProductionExecutor2-1：close_decrease_interval从100改成20（316行）（439w）

    ProductionExecutor-1：增加超跌过滤逻辑open_filter（抑制）+止盈（100改20）（475w）
    ProductionExecutor-2：增加超跌过滤逻辑open_filter（抑制+增强）（472w）
    ProductionExecutor-3：平仓阈值判定+止盈（100改20）（438w）
    ProductionExecutor-4：超跌逻辑+动态阈值（508w）
    ProductionExecutor-5：超跌逻辑+动态盈利阈值（500w）
    ProductionExecutor-6：超跌逻辑+动态阈值+止盈（100改20）（527w）
    """

    print("Running backtest of {}...".format(portfolio))
    bt_dir = 'BT_SP/CB/bt_info/{}-{}/{}'.format(st_date, ed_date, portfolio)  # 原始数据路径
    trigger_json_dir = 'cv/CB/cv-20200315-20200529_20200601-WuKong-50-100_big_cb_stock_20200301_20200413_2'  # 触发阈值路径
    signal_csv_dir = "big_cb_stock_20200301_20200413"  # 信号库名
    output_dir = "{}/{}".format(dir_name, result_dir_name)  # 输出结果路径

    symbols, init_quantities = load_symbols_and_quantities(bt_dir, portfolio)
    bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, mode, max_tasks=2)
    analyze_result(portfolio, st_date + "-" + ed_date, output_dir, result_dir_name, bt_dir, dir_name)

    print("End")


def load_symbols_and_quantities(bt_dir, portfolio, code=None):
    symbols, init_quantities = hf.get_symbols_quantities_from_json('{}/{}_quantity.json'.format(bt_dir, portfolio))
    print(symbols)
    print(init_quantities)
    # 如果只load单只股票（用于debug）
    if code is not None:
        for i in range(len(symbols)):
            if symbols[i] == code:
                symbols, init_quantities = [symbols[i]], [init_quantities[i]]
                break
    symbols, init_quantities = symbols[0:4], init_quantities[0:4]a
    symbols = ['110031.SH', '110048.SH', '110062.SH', '113009.SH', '113020.SH', '113029.SH', '113505.SH', '113520.SH', '113543.SH', '113553.SH', '113566.SH', '113576.SH', '123012.SZ', '123022.SZ', '123031.SZ', '123038.SZ', '123048.SZ', '127007.SZ', '127016.SZ', '128030.SZ', '128041.SZ', '128050.SZ', '128065.SZ', '128075.SZ', '128083.SZ', '128090.SZ', '128099.SZ', '128105.SZ', '110034.SH', '110051.SH', '110065.SH', '113011.SH', '113021.SH', '113031.SH', '113508.SH', '113521.SH', '113544.SH', '113555.SH', '113568.SH', '113577.SH', '123014.SZ', '123024.SZ', '123032.SZ', '123040.SZ', '123049.SZ', '127008.SZ', '128015.SZ', '128032.SZ', '128043.SZ', '128051.SZ', '128066.SZ', '128077.SZ', '128084.SZ', '128091.SZ', '128100.SZ', '128107.SZ', '110041.SH', '110052.SH', '110066.SH', '113013.SH', '113025.SH', '113032.SH', '113509.SH', '113526.SH', '113546.SH', '113556.SH', '113571.SH', '113578.SH', '123015.SZ', '123025.SZ', '123033.SZ', '123041.SZ', '123050.SZ', '127011.SZ', '128021.SZ', '128034.SZ', '128044.SZ', '128053.SZ', '128067.SZ', '128078.SZ', '128085.SZ', '128092.SZ', '128101.SZ', '110043.SH', '110056.SH', '110068.SH', '113014.SH', '113026.SH', '113033.SH', '113514.SH', '113534.SH', '113548.SH', '113562.SH', '113572.SH', '113579.SH', '123017.SZ', '123027.SZ', '123034.SZ', '123042.SZ', '127004.SZ', '127012.SZ', '128022.SZ', '128035.SZ', '128045.SZ', '128054.SZ', '128070.SZ', '128079.SZ', '128087.SZ', '128095.SZ', '128102.SZ', '110044.SH', '110057.SH', '110069.SH', '113017.SH', '113027.SH', '113034.SH', '113516.SH', '113537.SH', '113550.SH', '113563.SH', '113573.SH', '113581.SH', '123018.SZ', '123029.SZ', '123036.SZ', '123043.SZ', '127005.SZ', '127013.SZ', '128026.SZ', '128036.SZ', '128046.SZ', '128056.SZ', '128073.SZ', '128080.SZ', '128088.SZ', '128097.SZ', '128103.SZ', '110047.SH', '110059.SH', '113008.SH', '113019.SH', '113028.SH', '113504.SH', '113518.SH', '113542.SH', '113551.SH', '113565.SH', '113575.SH', '123002.SZ', '123020.SZ', '123030.SZ', '123037.SZ', '123047.SZ', '127006.SZ', '127015.SZ', '128028.SZ', '128040.SZ', '128048.SZ', '128063.SZ', '128074.SZ', '128081.SZ', '128089.SZ', '128098.SZ', '128104.SZ']
    init_quantities = [13920, 27340, 153110, 13720, 29420, 17180, 30150, 242140, 12370, 29300, 18050, 88750, 252150, 50850, 552480, 123900, 118710, 41240, 159060, 372860, 299520, 65540, 12210, 18090, 8570, 33460, 23910, 55370, 14150, 92490, 13520, 168190, 56990, 28740, 16350, 34000, 13980, 231550, 8330, 60520, 480780, 18680, 293640, 17320, 111910, 197540, 21310, 19260, 131390, 239220, 17930, 25050, 30980, 629490, 63060, 298570, 10890, 27260, 25220, 51430, 12570, 17200, 31640, 51480, 25480, 97420, 55190, 107720, 432620, 118000, 438550, 181570, 119160, 35420, 10700, 12760, 38200, 698300, 45120, 37850, 27310, 40460, 16360, 17620, 27310, 15010, 19140, 35460, 25980, 278780, 11670, 64640, 33540, 20060, 45240, 37840, 16220, 920500, 62210, 760970, 28740, 17650, 21810, 10770, 275740, 117720, 143620, 93150, 24620, 94990, 474370, 14650, 62420, 15960, 7900, 230080, 9340, 19110, 16820, 9290, 59470, 50130, 55470, 255210, 50210, 32660, 30850, 19660, 29900, 557430, 10420, 139960, 235610, 69700, 121320, 19260, 29460, 14710, 224360, 65920, 30730, 14190, 13980, 10900, 6960, 22400, 406520, 61680, 13170, 132750, 241720, 1230370, 53250, 11430, 128430, 126520, 19060, 20330, 15230, 115310, 14320, 37690, 32450, 82380]
 
    return symbols, init_quantities


if __name__ == '__main__':
    main()
