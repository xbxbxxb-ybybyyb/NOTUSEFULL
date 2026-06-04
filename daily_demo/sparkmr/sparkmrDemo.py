from os import path
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job
from xquant.compute.sparkmr import remote_print
from xquant.compute.sparkmr import trading_day
from xquant.marketdata import MarketData
from TaskMeta import TaskMeta


class sparkmrDemo:
    def __init__(self):
        # 并行化作业的名称
        self.__app_name = "sparkmrDemo"
        # 并行化作业的输出结果目录，该目录是HDFS上的目录，013150是用户工号
        self.__dst_dir = "013150/sparkmrDemo_Output"
        # 设置工程代码目录，工程代码目录指的是该程序代码的目录
        self.__env_dir = path.dirname(path.abspath(__file__))

    def start(self):
        stock_list = ['600587.SH', '600588.SH', '600589.SH', '600997.SH', '600998.SH',
                  '600999.SH', '601002.SH', '601007.SH', '601163.SH', '601218.SH']
        date_list = trading_day(20181201, 20181231)
        taskmeta_list = []
        for stock in stock_list:
            for date in date_list:
                taskmeta_list.append(TaskMeta(stock, date))
        config = Configuration()
        config.set_app_name(self.__app_name)
        config.set_dst_dir(self.__dst_dir)
        config.set_env_dir(self.__env_dir)
        job = Job(config, mode="OverWrite")
        job.add_tasks(taskmeta_list)
        job.set_func(self.func)
        job.start()

    def func(self, context, taskmeta):
        stock = taskmeta.get_stock()
        date = taskmeta.get_date()
        #注意：MarketData初始化时需传入hdfs连接，如下所示
        mdp = MarketData(dfs=context.get_hdfs())
        df = mdp.get_data_by_date('Stock', stock, date)
        df.index = df['MDDate'] + df['MDTime']
        remote_print(stock, date, len(df))
        context.save_as_pickle(df, '{}.pickle'.format(stock))
