"""SignalCV运行的main函数————update @2021.8.3"""

from DataAPI.GetCodeVol import get_cb_code, get_index_code, get_all_code
import pandas as pd


def main():
    main_stock_intra()
    # main_stock_all()
    # main_stock_amt()
    # main_stock_1s()
    # main_stock()
    # main_stock_voting()
    # main_cb()
    # main_cb_voting()
    # main_cb_voting_1s()


def main_stock_1s():
    from BT.Dy_Triggers.SignalCV import Task
    suffix = ''

    st_date, ed_date = '20210715', '20220228'
    code_list = pd.read_excel('/data/user/015629/Share/StockPool/sh_stock_1s_stock_list.xlsx')['stock'].to_list()
    freq = "1"  # "147", "258", "1"
    signal_lib = 'Albest{}Signals_Channel'.format(freq)
    mock_lib = 'Channel{}STickDataLib'.format(freq)
    tag_lib = 'Albest{}Signals_Channel'.format(freq)
    strategy = 'Albest'

    save_path = f'/data/user/011668/CVTriggers/{strategy}/{signal_lib}{suffix}'
    Task(code_list, st_date, ed_date, strategy, signal_lib, save_path,
         tag_lib=tag_lib, mock_lib=mock_lib, is_add_mock=False, overwrite_params={'min_triggers': 15}).start(mode='spark')  # local, multi_processing, spark


def main_stock2():
    from BT.Dy_Triggers.SignalCV import Task
    suffix = ''

    st_date, ed_date = '20210715', '20220228'
    code_list = pd.read_excel('/data/user/015629/Share/StockPool/sh_stock_1s_stock_list.xlsx')['stock'].to_list()
    for freq in ['036', '147', '258']:
        signal_lib = 'Albest{}Signals_Channel'.format(freq)
        mock_lib = 'Channel{}STickDataLib'.format(freq)
        tag_lib = 'Albest{}Signals_Channel'.format(freq)
        strategy = 'Albest'

        save_path = f'/data/user/011668/CVTriggers/{strategy}/{signal_lib}{suffix}'
        Task(code_list, st_date, ed_date, strategy, signal_lib, save_path,
             tag_lib=tag_lib, mock_lib=mock_lib, is_add_mock=False).start(mode='spark')  # local, multi_processing, spark


def main_stock():
    from BT.Dy_Triggers.SignalCV import Task
    suffix = '_hxj'
    st_date, ed_date = '20220101', '20220331'
    code_list = ["600111.SH", "600519.SH", "601012.SH", "002466.SZ", "300750.SZ", "002594.SZ", "300059.SZ", "000858.SZ", "002460.SZ", "601919.SH", "000792.SZ", "600905.SH", "600010.SH", "600438.SH", "300274.SZ", "600031.SH", "601318.SH", "600089.SH", "603799.SH", "603259.SH", "002176.SZ", "300014.SZ", "000723.SZ", "600703.SH", "600460.SH", "601899.SH", "000762.SZ", "000568.SZ", "002241.SZ", "300142.SZ", "603986.SH", "600036.SH", "000831.SZ", "002340.SZ", "002074.SZ", "002407.SZ", "000725.SZ", "300339.SZ", "601888.SH", "002129.SZ", "000625.SZ", "002475.SZ", "600096.SH", "600276.SH", "002709.SZ", "600030.SH", "600893.SH", "002240.SZ", "601600.SH", "600958.SH", "600809.SH", "002326.SZ", "600702.SH", "601669.SH", "600196.SH", "600887.SH", "600392.SH", "300343.SZ", "002714.SZ", "002371.SZ", "688981.SH", "002202.SZ", "000651.SZ", "000155.SZ", "000333.SZ", "601868.SH", "603993.SH", "000776.SZ", "002497.SZ", "002812.SZ", "300760.SZ", "000063.SZ", "600309.SH", "603501.SH", "000009.SZ", "000591.SZ", "600418.SH", "002610.SZ", "600338.SH", "000661.SZ", "600141.SH", "300015.SZ", "600884.SH", "002049.SZ", "601166.SH", "000002.SZ", "603026.SH", "000338.SZ", "300122.SZ", "300124.SZ", "300207.SZ", "002415.SZ", "000001.SZ", "000422.SZ", "600436.SH", "000799.SZ", "600150.SH", "600745.SH", "600584.SH", "601615.SH"]
    strategy = 'Albest'
    signal_lib = 'ray_albest_20211101_20211116'  # Everest20210201_20210515, ray_albest_20210201_20210520
    save_path = f'/data/user/011668/CVTriggers/{strategy}/{signal_lib}{suffix}'
    # save_path = 'lib'
    Task(code_list, st_date, ed_date, strategy, signal_lib, save_path, is_add_mock=False).start(mode='spark')  # local, multi_processing, spark


def main_stock_lst():
    from BT.Dy_Triggers.SignalCV import Task
    st_date, ed_date = '20210901', '20211231'
    code_list = get_index_code('hs300', '20220104')
    strategy = 'Albest'
    signal_lib = 'ray_albest_20210701_20210912_VolumeAmp'  # Everest20210201_20210515, ray_albest_20210201_20210520
    # save_path = f'/data/user/011668/CVTriggers/{strategy}/{signal_lib}{suffix}'
    save_path = 'lib'
    Task(code_list, st_date, ed_date, strategy, signal_lib, save_path, is_add_mock=False).start(mode='spark')  # local, multi_processing, spark
    # zz_index_cyb_stock_list.xlsx


def main_stock_intra():
    from BT.Dy_Triggers.SignalCVIntra import Task
    st_date, ed_date = '20220517', '20220517'
    code_list = get_index_code('800', '20220104')
    code_list = [x for x in code_list if x.endswith('.SZ')]
    code_list = ['300402.SZ']
    strategy = 'Albest'
    signal_lib = 'ray_albest_20211101_20211116_order'  # Everest20210201_20210515, ray_albest_20210201_20210520
    # save_path = f'/data/user/011668/CVTriggers/{strategy}/{signal_lib}{suffix}'
    save_path = 'lib'
    Task(code_list, st_date, ed_date, strategy, signal_lib, save_path, time_list=['10:00:00']).start(mode='local')  # local, multi_processing, spark


def main_cb_voting():
    from BT.Dy_Triggers.SignalCV_CB_Voting import Task
    # for signal_lib in ['ray_cb_stock_20210201_20210506_channel_02_2', 'ray_cb_stock_20210201_20210506_channel_00',
    #                    'ray_cb_stock_20210201_20210506_channel_02_l2p', 'ray_cb_stock_20210201_20210506']:
    for signal_lib in ['ray_cb_stock_20210501_20210506_sync_tick036']:
        st_date, ed_date = '20210601', '20211231'
        code_list = get_cb_code(st_date, ed_date)
        code_list = [x for x in code_list if x.endswith('.SZ')]
        save_path = f'/data/user/011668/CVTriggers/Kunlun/voting-{signal_lib}'
        Task(code_list, st_date, ed_date, signal_lib, tag_lib='CBFactor_Zeus_Super', save_path=save_path, is_add_mock=True).start(mode='spark')  # local, multi_processing, spark


def main_cb_voting_1s():
    from BT.Dy_Triggers.SignalCV_CB_Voting_1s import Task
    signal_tag_lib_list = [['ray_cb_stock_20210501_20210506_sync_channel_00', 'Factor_036_Channel_CB'],
                           ['ray_cb_stock_20210501_20210506_sync_channel_11', 'Factor_147_Channel_CB'],
                           ['ray_cb_stock_20210501_20210506_sync_channel_22', 'Factor_258_Channel_CB']]
    st_date, ed_date = '20210601', '20220314'
    code_list = get_cb_code(st_date, ed_date)
    code_list = [x for x in code_list if x.endswith('.SZ')]
    save_path = f'/data/user/011668/CVTriggers/Kunlun/voting-channel'
    Task(code_list, st_date, ed_date, signal_tag_lib_list, save_path=save_path, is_add_mock=True).start(mode='spark')  # local, multi_processing, spark


if __name__ == '__main__':
    main()
