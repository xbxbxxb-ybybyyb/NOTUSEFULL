import dolphindb as ddb
import json
import sys
import numpy as np
import time
sys.path.append("../")
import itertools
from AutoMiningFrame.FactorAutoMining.utils.setenv import get_env
from AutoMiningFrame.configs.local_connect import parse_connect

import os, sys
import datetime as dt
import re


class AutoMining:
    def __init__(self, start_date, end_date, securities, userID='K0321499', nonfactor_func={},
                 custom_func_path="",
                 study_scenario='stock', data_type='enhanced_tick'):
        """

        :param start_date:  开始日期，str，格式为YYYYMMDD，如'20220620'
        :param end_date:   结束日期，str，格式为YYYYMMDD，如'20220620'
        :param securities: list 股票列表，单标的支持str
        :param study_scenario: str 研究场景
        :param custom_func_path: str 用户自定义算子路径
        :param nonfactor_func: dict nonfactor名称和算子内容组成的dict

        """
        if isinstance(securities, str):
            securities = [securities]
        if not isinstance(securities, list):
            raise Exception("securities 需是 list 类型，单标的支持 str 类型")

        self.connect_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                "configs/connections.json")
        self.__check_date(start_date)
        self.__check_date(end_date)
        self.start_date = start_date
        self.end_date = end_date
        self.dol_start_date = self.start_date[:4] + '.' + self.start_date[4:6] + '.' + self.start_date[6:]
        self.dol_end_date = self.end_date[:4] + '.' + self.end_date[4:6] + '.' + self.end_date[6:]
        self.securities = securities
        self.userID = userID
        self.env = get_env()
        self.study_scenario = study_scenario
        self.data_type = data_type if data_type else 'enhanced_tick'
        self.nonfactor_func = nonfactor_func
        self.sess = self.__set_connection()
        self.sess.run("use DolphinFrame::FactorProvider")
        self.sess.run("use DolphinFrame::DataManager")
        self.sess.run("use ta")
        self.__load_depend_data(self.sess)
        if os.path.exists(custom_func_path):
            for root, _, files in os.walk(custom_func_path):
                for file in files:
                    self.sess.run("file_parse = file('{}')".format(os.path.join(root, file)))
                    temp = self.sess.run("file_parse.readLines()")
                    script_factor = "\n".join(i for i in temp)
                    self.sess.run(script_factor)

    def __set_connection(self):
        sess = ddb.session()
        ip, port, user, passsword = parse_connect()
        sess.connect(ip, port, user, passsword)
        return sess

    def __get_user_id(self):
        xquant_conf = os.popen("cat /etc/.config/xquant_conf")
        config = xquant_conf.read().split("\n")
        userid = None
        for con in config:
            if "userId" in con:
                userid = con.split("=")[1]
        if not userid:
            raise Exception("未找到userID，请检查环境！")
        return userid

    def __check_date(self, date):
        if len(date) != 8:
            raise Exception("{}:时间格式错误, 请使用正确格式,如20200802".format(date))
        try:
            dt.datetime.strptime(date, '%Y%m%d')
        except BaseException:
            raise Exception("{}:时间格式错误".format(date))

    def __check_factor_func(self, factor_func, sess):
        if isinstance(factor_func, str):
            factor_func = [factor_func]
        if not isinstance(factor_func, list):
            raise Exception("factor_func 为list类型，单个factor_func支持str")

        # 根据标的后缀 判断是上交所还是深交所标的
        if isinstance(self.securities, list):
            exchange_house = self.securities[0].split(".")[1].lower()
        elif isinstance(self.securities, str):
            exchange_house = self.securities.split(".")[1].lower()
        data_type_transfer = {'enhanced_tick': 'tick_enhanced', 'trade': 'trade'}
        table_name = exchange_house + "_" + self.study_scenario + "_" + data_type_transfer[self.data_type]

        script_load_data = f'''
        input_data_temp = getMarketData_Remote(stock={self.securities}, startTime=2022.10.18, endTime=2022.10.18, 
                                               tableName=`{table_name})
        input_data_temp = select * from input_data_temp order by concatDateTime(M_MDDate, M_MDTime) as timestamp
        '''
        sess.run(script_load_data)
        if self.nonfactor_func:
            if not isinstance(self.nonfactor_func, dict):
                raise Exception("参数nonfactor_func必须是dict格式的参数")
            else:
                nonfactor_fomula = [i for i in self.nonfactor_func.values()]
                nonfactor_name = [k for k, v in self.nonfactor_func.items() if v in nonfactor_fomula]
                new_columns_list = []
                for i in range(len(nonfactor_fomula)):
                    temp = nonfactor_name[i] + "=" + nonfactor_fomula[i]
                    new_columns_list.append(temp)
                new_columns = ",".join([i for i in new_columns_list])
                scripts_temp_input_data = f"""update input_data_temp set {new_columns}"""
                self.sess.run(scripts_temp_input_data)


        passed_factor_func = []
        start = time.time()
        for factor in factor_func:
            try:
                script = f'''factorData = select M_HTSCSecurityID, concatDateTime(M_MDDate, M_MDTime) as timestamp, {factor} as factor \
                         from input_data_temp context by M_MDDate
                         '''
                sess.run(script)
                passed_factor_func.append(factor)
            except RuntimeError as e:
                print("[Automining] 未通过校验表达式： {}， 未通过原因：{}".format(factor, str(e).split("=>")[1] if "=>" in str(e) else str(e)))
        end = time.time()
        print("[Automining] 校验完成，共{}个因子表达式，{}通过校验, 耗时：{}s".format(len(factor_func),
                                                                                   len(passed_factor_func),
                                                                                    end-start))
        return passed_factor_func

    def __load_depend_data(self, sess):
        """

        :param factor_func: 因子逻辑，str类型，直接传给select
        :return:
        """
        self.factor_dic = {}
        # 根据标的后缀 判断是上交所还是深交所标的
        if isinstance(self.securities, list):
            exchange_house = self.securities[0].split(".")[1].lower()
        elif isinstance(self.securities, str):
            exchange_house = self.securities.split(".")[1].lower()
        data_type_transfer = {'enhanced_tick': 'tick_enhanced', 'trade': 'trade'}
        table_name = exchange_house + "_" + self.study_scenario + "_" + data_type_transfer[self.data_type]
        # 加载数据
        script_load_data = f'''
        input_data = getMarketData_Remote(stock={self.securities}, startTime={self.dol_start_date}, 
                                             endTime={self.dol_end_date}, tableName=`{table_name})
        input_data = select * from input_data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or \
                                                    (M_MDTime>=13:00:00 and M_MDTime<=14:57:00)
        '''
        sess.run(script_load_data)

        # 数据过滤
        if 'tick' in table_name:
            market_data_threshold = 3000
            script_filter = f"""
                need_select = select M_MDDate, M_HTSCSecurityID from input_data group by M_MDDate, M_HTSCSecurityID \
                having count(*)>={market_data_threshold}
                input_data = select * from ej(input_data, need_select, `M_HTSCSecurityID`M_MDDate)
            """
            sess.run(script_filter)

        if not self.nonfactor_func:
            return
        else:
            if not isinstance(self.nonfactor_func, dict):
                raise Exception("参数nonfactor_func必须是dict格式的参数")
            else:
                nonfactor_fomula = [i for i in self.nonfactor_func.values()]
                passed_nonfactor_fomula = self.__check_factor_func(nonfactor_fomula, self.sess)
                passed_nonfactor_name = [k for k, v in self.nonfactor_func.items() if v in passed_nonfactor_fomula]
                new_columns_list = []
                for i in range(len(passed_nonfactor_fomula)):
                    temp = passed_nonfactor_name[i] + "=" + passed_nonfactor_fomula[i]
                    new_columns_list.append(temp)
                new_columns = ",".join([i for i in new_columns_list])
                scripts_temp_input_data = f"""update input_data set {new_columns}"""
                self.sess.run(scripts_temp_input_data)

    def __gen_load_factor_func(self, factor_func, sess):
        """

        :param factor_func: 因子逻辑，str类型，直接传给select
        :return:
        """
        if isinstance(factor_func, str):
            factor_func = [factor_func]
        if not isinstance(factor_func, list):
            raise Exception("factor_func 为list类型，单个factor_func支持str")
        factor_func_alias = ""
        self.factor_dic = {}
        for i in range(len(factor_func)):
            self.factor_dic['f' + str(i + 1)] = factor_func[i]
            factor_func_alias += factor_func[i] + ' as ' + 'f' + str(i + 1) + ','
        factor_func_alias = factor_func_alias[:-1]

        script = f'''factorData = select M_HTSCSecurityID, concatDateTime(M_MDDate, M_MDTime) as timestamp, {factor_func_alias} \
                     from input_data context by M_MDDate, M_HTSCSecurityID
                     '''
        sess.run(script)

    def __load_label_data(self, label_names, sess):
        """

        :param label_names: 根据标签名
        :param userID: 用户ID
        :return:
        """
        self.label_dic = {}
        for i in range(len(label_names)):
            self.label_dic['f' + str(i + 1)] = label_names[i]

        dol_label_names = ''
        for label in label_names:
            dol_label_names += '`' + label
        script = f'''
        labelData = load_data_from_dfs_remote(symbol={self.securities},factor_name_list={dol_label_names},\
        time_begin={self.dol_start_date},time_end={self.dol_end_date},\
        factor_type=`label, source_type='public', data_type='{self.data_type}')
        '''
        sess.run(script)

    def __gen_load_fitness_func(self, fitness_path, fitness_names, sess):
        """
        load 适应度函数
        :param fitness_path: 适应度函数路径
        :param fitness_names: 适应度函数名称
        :return:
        """
        self.fitness_dic = {}
        for i in range(len(fitness_names)):
            self.fitness_dic['fit' + str(i + 1)] = fitness_names[i]

        for fitness_name in fitness_names:
            fitness_dos_file = os.path.join(fitness_path, fitness_name + ".dos")
            if not os.path.exists(fitness_dos_file):
                raise Exception("未找到对应的适应度函数文件！ {}".format(fitness_dos_file))

            sess.run("file_parse = file('{}')".format(fitness_dos_file))
            temp = sess.run("file_parse.readLines()")
            script_factor = "\n".join(i for i in temp)
            sess.run(script_factor)

    def load_factor_data_by_express(self, factor_func):
        self.sess.run("use DolphinFrame::FactorProvider")
        self.sess.run("use DolphinFrame::DataManager")
        self.sess.run("use ta")
        self.__gen_load_factor_func(factor_func, self.sess)
        factorData = self.sess.run("factorData")
        factorData.rename(columns=self.factor_dic, inplace=True)
        return factorData

    def execute_fitness_func(self, factor_func, label_names, fitness_path, fitness_names, fitness_reform_method=None):
        if isinstance(fitness_names, str):
            fitness_names = [fitness_names]
        if not isinstance(fitness_names, list):
            raise Exception("fitness_names 需是 list 类型，单适应度函数支持 str 类型")
        if isinstance(label_names, str):
            label_names = [label_names]
        if not isinstance(label_names, list):
            raise Exception("label_names 需是 list 类型，单标签支持 str 类型")

        #sess = self.__set_connection()
        # self.sess.run("use DolphinFrame::FactorProvider")
        # self.sess.run("use DolphinFrame::DataManager")
        # self.sess.run("use ta")
        factor_func = self.__check_factor_func(factor_func, self.sess)
        self.__gen_load_factor_func(factor_func, self.sess)
        self.__load_label_data(label_names, self.sess)
        self.__gen_load_fitness_func(fitness_path, fitness_names, self.sess)
        nan_factordata_threshold = 0.2
        script_data_manager = f'''
        //factorData = unpivot(factorData, `M_HTSCSecurityID`timestamp, factorData.schema().colDefs.name[2:]).rename!(`M_HTSCSecurityID`timestamp`factorName`factorValue)
        //labelData = unpivot(labelData, `M_HTSCSecurityID`timestamp, labelData.schema().colDefs.name[3:]).rename!(`M_HTSCSecurityID`timestamp`labelName`labelValue)
        // 查看nan值比例
        all_factors = (set(factorData.colNames())-set(['M_HTSCSecurityID','timestamp'])).keys()
        for (a in all_factors){{
            res = "select * from (select sum("+a+".isNull())\\\count(*) as factor_nan  from factorData group by M_HTSCSecurityID, date(timestamp) as M_MDDate) where factor_nan>={nan_factordata_threshold}"
            need_delete = parseExpr(res).eval()
            filter = dict(need_delete.M_MDDate, need_delete.M_HTSCSecurityID)
            sqlUpdate(table=factorData, updates=sqlColAlias(<NONE>, a), where=<conditionalFilter(M_HTSCSecurityID,date(timestamp) , filter)>).eval()
        }}
        factorLabelData = lj(factorData, labelData, `M_HTSCSecurityID`timestamp).sortBy!(`M_HTSCSecurityID`timestamp)
        factorData = NULL
        labelData = NULL
        '''
        self.sess.run(script_data_manager)
        factor_tuple = [(k, v) for k, v in self.factor_dic.items()]
        label_tuple = [(k, v) for k, v in self.label_dic.items()]
        factor_label_names = [d for d in itertools.product(factor_tuple, label_tuple)]
        select_args = ""
        for fitn, fitname in self.fitness_dic.items():
            for factor_tuple, label_tuple in factor_label_names:
                select_args += fitname + "({}, {}) as {},".format(factor_tuple[0], label_tuple[1],
                                                                  factor_tuple[0] + "_" + label_tuple[0] + "_" + fitn)
        select_args = select_args[:-1]
        script_calc_fitness = f"""
            fitnessdata = select M_HTSCSecurityID, distinct(date(timestamp)) as MDDate, {select_args} from factorLabelData group by M_HTSCSecurityID, date(timestamp) as MDDate
            fitnessdata
            """
        fitness_data = self.sess.run(script_calc_fitness)

        # 当起止日期期间的 nan值比例超过30  则赋值全nan 然后对nan值填充-999
        fitness_cols = sorted(list(set(fitness_data.columns.to_list()) - {'M_HTSCSecurityID', 'MDDate'}))
        stocks = fitness_data['M_HTSCSecurityID'].unique()
        nan_threshold = 0.3
        for stock in stocks:
            for col in fitness_cols:
                num = fitness_data[fitness_data['M_HTSCSecurityID']==stock][col].isna().sum()  # nan个数
                if num / len(fitness_data[fitness_data['M_HTSCSecurityID']==stock]) > nan_threshold:
                    fitness_data[fitness_data['M_HTSCSecurityID']==stock].loc[:,col] = -999  # 占比
        fitness_data = fitness_data.set_index(['M_HTSCSecurityID', 'MDDate']).stack().reset_index()
        fitness_data.columns = ['M_HTSCSecurityID', 'MDDate', 'fitname', 'fitValue']
        fitness_data[['factor', 'label', 'fitness']] = fitness_data['fitname'].str.split("_", expand=True)
        fitness_data['factor'] = fitness_data['factor'].map(self.factor_dic)
        fitness_data['label'] = fitness_data['label'].map(self.label_dic)
        fitness_data['fitness'] = fitness_data['fitness'].map(self.fitness_dic)
        del fitness_data['fitname']
        # fitness_data = fitness_data.rename(columns=rename_dict)
        # fitness_data.replace(self.dic, inplace=True)
        if not fitness_reform_method:
            return fitness_data
        elif fitness_reform_method == 'mean':
            return fitness_data.groupby(['M_HTSCSecurityID', 'factor', 'label', 'fitness']).mean()
        elif fitness_reform_method.upper() == "IR":
            return fitness_data.groupby(['M_HTSCSecurityID', 'factor', 'label', 'fitness']).mean()/fitness_data.groupby(['M_HTSCSecurityID', 'factor', 'label', 'fitness']).std()


if __name__ == '__main__':
    # 初始化
    # am = AutoMining(start_date='20220620', end_date='20220630', securities=['688599.SH'])
    # 因子挖掘接口、因子评测接口
    # res = am.execute_fitness_func(fitness_path='/app/dolphindb/server/modules/FitnessFunc',
    #                              fitness_names=["AnalyzerIC", "AnalyzerICCopy"], fitness_reform_method='mean',
    #                              label_names=['labelEQendtaggertypeEQmidpricedsizeEQ300',
    #                                           'labelEQendtaggertypeEQmidpricedsizeEQ300Copy'],
    #                              factor_func=["add(M_LastPx, M_MinPx)", "add(M_LastPx, M_MaxPx)", "sub(M_LastPx, M_MinPx)"])
    # print(res)

    # res = am.execute_fitness_func(fitness_path='/app/dolphindb/server/modules/FitnessFunc',
    #                              fitness_names=["AnalyzerIC", "AnalyzerICCopy"],
    #                              label_names=['labelEQendtaggertypeEQmidpricedsizeEQ300',
    #                                           'labelEQendtaggertypeEQmidpricedsizeEQ300Copy'],
    #                              factor_func=["add(M_LastPx, M_MinPx)", "add(M_LastPx, M_MaxPx)", "sub(M_LastPx, M_MinPx)"])

    # print(res.head())
    #
    # 因子计算接口
    # res = am.load_factor_data_by_express(["add(M_LastPx, M_MinPx)", "add(M_LastPx, M_MaxPx)", "sub(M_LastPx, M_MinPx)"])
    # print(res.head())
    import time

    am = AutoMining(userID='016884',start_date='20220410', end_date='20220610', securities=['510300.SH'],
                    custom_func_path="./custom_func/", nonfactor_func={'NegMLastPx':'neg(M_LastPx)', 'LogMLastPx':'log(M_LastPx)'},
                    study_scenario='fund')

    gp = [
        'mcovar(mkurtosis(div(sub(M_TotalOfferQty, M_BuyQty), mavg(M_TotalBidQty,40)),30), mmin(log(msum(M_TotalBidQty,40)),10),20)',
        'min(max(min(min(M_BuyQty, M_LastPx), abs(M_BuyMoney)), ratio(div(M_SellQty, M_TotalBidQty), mmax(M_BuyQty,10))), abs(mul(mcorr(M_BuyQty, M_TotalOfferQty,40), mul(M_NumTrades, M_NumTrades))))',
        'log(M_BuyMoney)',
        'mcovar(sqrt(add(M_BuyQty, M_TotalBidQty)), mmin(log(M_NumTrades),10),40)',
        'mul(min(mkurtosis(mcorr(M_LastPx, M_NumTrades,50),30), msum(neg(M_BuyMoney),50)), neg(mavg(abs(M_LastPx),30)))',
        'mmin(sub(M_TotalBidQty, M_TotalOfferQty),50)',
        'mcovar(msum(ratio(sqrt(M_TotalOfferQty), mcorr(M_TotalOfferQty, M_TotalBidQty,30)),50), sub(add(sub(M_NumTrades, M_BuyQty), log(M_TotalBidQty)), div(max(M_BuyQty, M_BuyMoney), mskew(M_BuyQty,10))),50)',
        'neg(mkurtosis(mcorr(M_SellMoney, M_BuyQty,50),10))',
        'log(abs(abs(abs(M_BuyQty))))',
        'abs(min(M_BuyQty, mmax(M_LastPx,40)))',
        'log(max(M_BuyMoney, M_BuyMoney))',
        'mcovar(sqrt(M_BuyMoney), log(M_TotalOfferQty),40)',
        'log(min(msum(sub(M_SellMoney, M_SellMoney),40), msum(div(M_LastPx, M_BuyQty),20)))',
        'min(mskew(mmin(M_BuyQty,10),40), neg(mskew(abs(M_SellMoney),20)))',
        'sub(mmin(M_TotalOfferQty,10), M_TotalOfferQty)',
        'min(max(M_BuyMoney, M_NumTrades), add(M_TotalBidQty, M_BuyQty))',
        'log(mmin(M_BuyMoney,30))',
        'mkurtosis(add(M_NumTrades, neg(M_SellQty)),50)',
        'mcorr(mul(M_TotalBidQty, M_SellMoney), M_BuyQty,30)',
        'min(M_TotalOfferQty, mkurtosis(mskew(M_TotalOfferQty,50),40))',
        'mcorr(mavg(mskew(M_BuyMoney,50),10), add(mcorr(M_BuyQty, M_TotalOfferQty,20), mul(M_TotalBidQty, M_TotalOfferQty)),20)',
        'sub(M_TotalBidQty, mavg(add(M_LastPx, M_LastPx),30))',
        'mcovar(mcorr(M_BuyQty, min(mul(M_TotalOfferQty, M_BuyQty), M_SellQty),20), max(M_TotalOfferQty, min(div(M_TotalBidQty, M_SellQty), abs(M_TotalOfferQty))),50)',
        'mul(sqrt(mavg(M_SellMoney,40)), log(mul(M_TotalBidQty, M_BuyMoney)))',
        'ratio(max(M_BuyMoney, M_TotalBidQty), msum(M_BuyMoney,50))',
        'abs(msum(ratio(M_BuyMoney, M_BuyQty),10))',
        'mmin(mmax(M_SellMoney,50),50)',
        'sub(mmin(add(M_TotalBidQty, M_TotalOfferQty),30), mcorr(mcovar(M_TotalOfferQty, M_SellQty,40), sub(M_NumTrades, M_TotalBidQty),30))',
        'mmin(M_SellMoney,10)',
        'mmax(mmin(M_BuyQty,50),30)',
        'sqrt(mkurtosis(M_TotalOfferQty,10))',
        'mul(max(mmin(sub(M_SellQty, M_SellMoney),20), add(mul(M_BuyQty, M_SellMoney), sqrt(M_BuyQty))), div(ratio(neg(M_BuyQty), msum(M_BuyQty,30)), sub(sub(M_BuyQty, M_BuyQty), msum(M_TotalBidQty,40))))',
        'msum(add(neg(M_BuyQty), mcorr(M_SellMoney, M_SellQty,40)),10)',
        'min(div(M_BuyQty, M_BuyQty), min(M_BuyMoney, M_SellQty))',
        'mkurtosis(add(msum(M_BuyMoney,50), div(M_BuyMoney, M_TotalOfferQty)),10)',
        'mul(add(msum(ratio(M_SellMoney, M_SellMoney),30), abs(add(M_TotalBidQty, M_BuyMoney))), mkurtosis(abs(sub(M_SellQty, M_SellMoney)),50))',
        'min(mcovar(sqrt(M_TotalOfferQty), mkurtosis(M_SellQty,50),40), neg(mul(M_LastPx, M_NumTrades)))',
        'add(ratio(mkurtosis(M_TotalBidQty,40), div(M_TotalBidQty, M_TotalBidQty)), abs(mskew(M_TotalBidQty,10)))',
        'mskew(add(msum(ratio(M_SellQty, M_NumTrades),50), log(msum(M_SellMoney,20))),20)',
        'mkurtosis(abs(M_NumTrades),40)']
    # gp = ['log(M_BuyMoney)', 'mcovar(mkurtosis(div(sub(M_TotalOfferQty, M_BuyQty), mavg(M_TotalBidQty,40)),30), mmin(log(msum(M_TotalBidQty,40)),10),20)']
    gp = ['add(NegMLastPx, M_LastPx)', 'abs(NegMLastPx)', 'mmin(LogMLastPx,10)']
    print(len(gp))
    time_sta = time.time()
    res = am.execute_fitness_func(fitness_path='/opt/anaconda3/lib/python3.6/site-packages/AutoMiningFrame/FactorAutoMining/fitness_file',
                                  fitness_names=["AnalyzerIC"],
                                  fitness_reform_method='mean',
                                  label_names=['labelEQendtaggertypeEQmidpricedsizeEQ120'],
                                  factor_func=gp
                                  ).reset_index().fillna(-999)

    print(time.time() - time_sta)
    print(res)

