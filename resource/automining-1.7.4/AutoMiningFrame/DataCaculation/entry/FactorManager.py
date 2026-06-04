import dolphindb as ddb
import os
import pymysql
from xquant.factordata import FactorData
from AutoMiningFrame.DataCaculation.utils.setenv import get_env
from AutoMiningFrame.DataCaculation.utils.common_utils import check_date
from AutoMiningFrame.configs.local_connect import parse_connect
from tqdm import trange
import numpy as np
from datetime import datetime
import pandas as pd

fd = FactorData()


class FactorProvider:
    def __init__(self, userID=None):
        self.s = ddb.session()
        host, port, userid, password = parse_connect()
        self.host = host
        self.port = port
        self.userid = userid
        self.password = password
        self.online_factor_path = "xquant@168.61.13.40::dolphin_factor"
        self.online_label_path = "xquant@168.61.13.40::dolphin_label"
        self.env = get_env()
        if self.env == 'prd':
            self.s.connect(host=self.host, port=self.port, userid=self.userid, password=self.password)
        else:
            self.s.connect(host=self.host, port=self.port, userid=self.userid, password=self.password)
        self.userID = userID if userID else self.__get_user_id()

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

    # 因子元数据注册接口

    def upload_factor_meta(self, upload_values_dict, table_type='personal', to_sql=False):
        """
        :param sql_config:
        :param upload_values_dict:
        :param factor_type:
        :return:
        """
        if to_sql:
            sql_config = self._set_sql_config()
            if table_type == 'personal':
                table_name = 'factor_personal_meta_tbl'
            elif table_type == 'public':
                table_name = 'factor_public_meta_tbl'
            else:
                raise Exception("未检测到合格的factor_type")
            conn = pymysql.connect(**sql_config)
            cur = conn.cursor()
            COLstr = ""
            ROWstr = ""
            Updatestr = ""
            for k in upload_values_dict.keys():
                COLstr = COLstr + ' ' + k + ','
                ROWstr = (ROWstr + '"%s"' + ',') % (upload_values_dict[k])
                if k not in ['FactorName', 'FactorAuthor']:
                    Updatestr = Updatestr + " " + k + "='" + upload_values_dict[k] + "'" + ","

            try:
                vsql = "INSERT INTO %s(%s) VALUES(%s) ON DUPLICATE KEY UPDATE %s" % (
                    table_name, COLstr[:-1], ROWstr[:-1], Updatestr[:-1])
                cur.execute(vsql)
                conn.commit()
                cur.close()
                conn.close()
                return True
            except pymysql.err.OperationalError as e:
                conn.rollback()
                print("数据插入失败：{}".format(e))
                cur.close()
                conn.close()
                return False
            except Exception as e:
                conn.rollback()
                print("数据插入失败：{}".format(e))
                cur.close()
                conn.close()
                return False
        else:
            import datetime
            author = upload_values_dict['FactorAuthor']
            root_path = "/data/user/016869/AutoMiningFrame/factor_{}_meta_tbl/{}".format(table_type, author)
            if not os.path.exists(root_path):
                os.mkdir(root_path)
            cur_date = datetime.datetime.now().strftime("%Y%m%d")
            file_name = os.path.join(root_path, cur_date + ".csv")
            old_df = pd.DataFrame()
            if os.path.exists(file_name):
                old_df = pd.read_csv(file_name)
            new_df = old_df.append(pd.Series(upload_values_dict).to_frame().T)
            new_df.to_csv(file_name, index=False)

        return

    def load_factor_meta(self, table_type='personal', data_type='enhanced_tick', factor_list=None, use_sql=True):
        fdd = FactorData()
        start_date = "20220901"
        end_date = datetime.now().strftime("%Y%m%d")
        date_list = fdd.tradingday(start_date, end_date)

        factor_type = 'factor'
        if not factor_list:
            fac = self.load_info_from_dfs(factor_type, source_type=table_type, data_type=data_type)
        else:
            if not isinstance(factor_list, list):
                factor_list = [factor_list]
            fac = factor_list
        if not use_sql:
            df_res = pd.DataFrame()
            for root, dir, files in os.walk("/data/user/016869/AutoMiningFrame/factor_{}_meta_tbl/".format(table_type)):
                for file in files:
                    file_total_path = os.path.join(root, file)
                    file_date = file.split(".")[0]
                    file_user_id = file_total_path.split("/")[-2]
                    if file_date in date_list and self.userID == file_user_id:
                        df = pd.read_csv(file_total_path)
                        df_res = df_res.append(df)
            if df_res.empty:
                return
            df_res = df_res.drop_duplicates(['FactorName', 'LabelName'])
            df_res = df_res[df_res['FactorName'].isin(fac)]
            return df_res
        else:
            sql_config = self._set_sql_config()
            if table_type == 'personal':
                table_name = 'factor_personal_meta_tbl'
            elif table_type == 'public':
                table_name = 'factor_public_meta_tbl'
            else:
                raise Exception("未检测到合格的factor_type")
            conn = pymysql.connect(**sql_config)
            cur = conn.cursor()
            cur.execute("select * from {} where FactorName in {}".format(table_name,
                                                                         str(set(fac)).replace("{", "(").replace("}",
                                                                                                                 ")")))
            cols = [i[0] for i in cur.description]
            result = cur.fetchall()
            res_df = pd.DataFrame(list(result), columns=cols)
            cur.close()
            conn.close()
            # TODO: 需要一个数据库的接口

            return res_df

    def _set_sql_config(self):
        if self.env == 'uat':
            sql_config = {'host': '168.61.32.84',
                          'user': 'root',
                          'passwd': '123456',
                          'db': 'strategycenter  ',
                          'port': 3306,
                          'charset': 'utf8'}
        elif self.env == 'prd':
            sql_config = {'host': '168.11.34.94',
                          'user': 'xquant',
                          'passwd': 'b%GW0Z8mt#7uY8@w',
                          'db': 'strategy_center',
                          'port': 3308,
                          'charset': 'utf8'}
        else:
            raise Exception("未检测到合格的env")
        return sql_config

    def upload_factor_analysis_res(self, user_id, analysis_df, table_type='personal', to_sql=False):
        if to_sql:
            sql_config = self._set_sql_config()
            if table_type == 'personal':
                table_name = 'factor_personal_analysis_res'
            elif table_type == 'public':
                table_name = 'factor_public_analysis_res'
            else:
                raise Exception("未检测到合格的factor_type")
            conn = pymysql.connect(**sql_config)
            cur = conn.cursor()

            analysis_df = analysis_df.replace([np.inf, -np.inf], 0)
            analysis_df = analysis_df.where(analysis_df.notna(), None)
            cols_list = analysis_df.columns.tolist()
            COLstr = ""
            ROWstr = ""
            Updatestr = ""

            for col in cols_list:
                COLstr += "`" + col + "`,"
                ROWstr += "%s,"
                Updatestr += "`" + col + "`" + "=%s,"
                analysis_df.loc[:, "new" + col] = analysis_df.loc[:, col]
            values = analysis_df.values.tolist()
            values = [tuple(lst) for lst in values]

            try:
                sql = "INSERT INTO %s(%s) select %s ON DUPLICATE KEY UPDATE %s" % (
                    table_name, COLstr[:-1], ROWstr[:-1], Updatestr[:-1])
                cur.executemany(sql, values)
                conn.commit()
                cur.close()
                conn.close()
                return True
            except pymysql.err.OperationalError as e:
                conn.rollback()
                print("数据插入失败：{}".format(e))
                cur.close()
                conn.close()
                return False
            except Exception as e:
                conn.rollback()
                print("数据插入失败：{}".format(e))
                cur.close()
                conn.close()
                return False
        else:
            import datetime
            author = user_id
            root_path = "/data/user/016869/AutoMiningFrame/factor_{}_analysis_res/{}".format(table_type, author)
            if not os.path.exists(root_path):
                os.mkdir(root_path)
            cur_date = datetime.datetime.now().strftime("%Y%m%d")
            file_name = os.path.join(root_path, cur_date + ".csv")
            old_df = pd.DataFrame()
            if os.path.exists(file_name):
                old_df = pd.read_csv(file_name)
            new_df = old_df.append(analysis_df)
            new_df.to_csv(file_name, index=False)
        return

    def load_factor_analysis_res(self, data_type='enhanced_tick', factor_list=None,
                                 start_date=None, end_date=None, stock=None, label_name=None):
        """
        :param data_type: "enhanced_tick" "tick_l2p"
        :param factor_list: 默认不传
        :param start_date: "20231101"
        :param end_date:   "20231101"
        :param stock:   不传 str  list 都可以
        :param label_name: str 只能一个
        :return:
        """
        factor_type = 'factor'
        if not factor_list:
            fac = list(self.load_info_from_dfs(factor_type, source_type='public', data_type=data_type))
        else:
            if not isinstance(factor_list, list):
                factor_list = [factor_list]
            fac = factor_list

        if not start_date:
            start_date = '2020.01.01'
        else:
            start_date = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
            end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]
        else:
            end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]
        if not stock:
            stock = "NULL"
        else:
            if isinstance(stock, str):
                stock = [stock]

        if not label_name:
            label_name = "NULL"

        res_df = self.s.run(f"""
                use DolphinFrame::FactorProvider
                //load_factor_analysis_res_remote(factor_list, start_date, end_date, stock_list, label_name, data_type)
                load_factor_analysis_res_remote(factor_list={fac}, start_date={start_date}, end_date={end_date}, 
                                                stock_list={stock}, label_name='{label_name}', data_type='{data_type}')
                """)
        return res_df

    # 获取因子发布状态信息
    def load_factor_upload_status(self, data_type='enhanced_tick'):
        factor_status = self.s.run(f"""
                        use DolphinFrame::FactorProvider
                        load_factor_upload_status_remote('{data_type}')""")
        res = factor_status[factor_status['status'] == 1]
        if res.shape[0] > 0:
            return False
        return True

    # 更新因子发布状态信息
    def insert_factor_upload_status(self, factor_name, user_id, status, data_type='enhanced_tick'):
        self.s.run(f"""
                        use DolphinFrame::FactorProvider
                        insert_factor_upload_status_remote('{factor_name}', '{user_id}', {status}, '{data_type}')""")
        return

    # 创建个人因子库
    def create_database_table(self, reCreateDB=False, reCreateFactorTB=False, reCreateLabelTB=False,
                              data_type='enhanced_tick'):
        """
        建个人库、表。
        如果该用户名下没有个人库，会直接新建个人库、因子表、标签表
        :param data_type: enhanced_tick or trade
        :param reCreateDB: bool类型，重建库，库下的因子表和标签表也会被删除重建
        :param reCreateFactorTB: bool类型。不重建库时，可单独重建因子表
        :param reCreateLabelTB: bool类型。不重建库时，可单独重建标签表
        :return:
        """

        reCreateDB = str(reCreateDB).lower()
        reCreateFactorTB = str(reCreateFactorTB).lower()
        reCreateLabelTB = str(reCreateLabelTB).lower()
        self.s.run("""use DolphinFrame::FactorProvider""")
        res = self.s.run(
            f"""create_factor_db_personal_remote('{self.userID}', {reCreateDB}, {reCreateFactorTB}, {reCreateLabelTB},'{data_type}')""")
        return res

    # 保存个人因子到个人库
    def save_personal_data_to_dfs(self, res, factor_type, data_type='enhanced_tick'):
        """

        :param data_type: enhanced_tick  or  trade
        :param res: 待保存数据，DataFrame，必须包含列：timestamp、M_HTSCSecurityID
        :param factor_type: 'factor' or 'label'
        :return:
        """
        res = res.rename(columns={'HTSCSecurityID': 'M_HTSCSecurityID'})
        if 'timestamp' not in res.columns or 'M_HTSCSecurityID' not in res.columns:
            raise Exception("待存储的数据中缺少timestamp或者M_HTSCSecurityID列")
        if 'R_HTSCSecurityID' in res.columns:
            del res['R_HTSCSecurityID']
        res['R_HTSCSecurityID'] = None
        data_columns = list(set(res.columns.to_list()) - {'timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID'})
        res = res[['timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID'] + data_columns]
        self.s.upload({'res': res})
        print('[FactorManager]upload done')
        res = self.s.run(f"""
                        use DolphinFrame::FactorProvider
                        res.replaceColumn!(`timestamp, timestamp(res.timestamp))
                        save_data_to_dfs_remote(res, '{factor_type}', '{data_type}', 'personal', '{self.userID}')""")
        return res

    # 保存公共因子/标签到公共库
    def save_public_data_to_dfs(self, res, factor_type, data_type='enhanced_tick'):
        res = res.rename(columns={'HTSCSecurityID': 'M_HTSCSecurityID'})
        if 'timestamp' not in res.columns or 'M_HTSCSecurityID' not in res.columns:
            raise Exception("待存储的数据中缺少timestamp或者M_HTSCSecurityID列")
        if 'R_HTSCSecurityID' in res.columns:
            del res['R_HTSCSecurityID']
        res['R_HTSCSecurityID'] = None
        data_columns = list(set(res.columns.to_list()) - {'timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID'})
        res = res[['timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID'] + data_columns]
        self.s.upload({'res': res})
        print('[FactorManager]upload done')
        res = self.s.run(f"""
                        use DolphinFrame::FactorProvider
                        res.replaceColumn!(`timestamp, timestamp(res.timestamp))
                        save_data_to_dfs_remote(res, '{factor_type}', '{data_type}', 'public', '{self.userID}')""")
        return res

    # 读取个人因子/标签库因子
    def load_personal_data_from_dfs(self, symbol=None, factor_list=None, start_time=None, end_time=None,
                                    factor_type=None,
                                    data_type='enhanced_tick'):
        if isinstance(symbol, str):
            symbol = [symbol]
        if isinstance(factor_list, str):
            factor_list = [factor_list]
        if not factor_list:
            factor_list = 'NULL'
        self.s.run("""use DolphinFrame::FactorProvider""")
        res_list = []
        dt_list = fd.tradingday(start_time, end_time)
        groups_limit = 100
        groups = len(dt_list) // groups_limit
        groups = 1 if groups == 0 else groups
        dt_groups = []
        for i in range(groups):
            if i != groups - 1:
                dt_groups.append((dt_list[i * groups_limit], dt_list[(i + 1) * groups_limit - 1]))
            else:
                dt_groups.append((dt_list[i * groups_limit], dt_list[-1]))
        for i in trange(len(dt_groups)):
            s, e = dt_groups[i]
            start_time = s[:4] + "." + s[4:6] + "." + s[6:]
            end_time = e[:4] + "." + e[4:6] + "." + e[6:]
            temp = self.s.run(
                f"load_data_from_dfs_remote({symbol},{factor_list},{start_time}, {end_time},'{factor_type}', '{data_type}',\
                         'personal','{self.userID}')")
            res_list.append(temp)
        res = pd.concat(res_list)
        return res

    # 读取公共因子/标签数据
    def load_public_data_from_dfs(self, symbol=None, factor_list=None, start_time=None, end_time=None, factor_type=None,
                                  data_type='enhanced_tick'):
        if isinstance(symbol, str):
            symbol = [symbol]
        if isinstance(factor_list, str):
            factor_list = [factor_list]
        if not factor_list:
            factor_list = 'NULL'
        self.s.run("""use DolphinFrame::FactorProvider""")
        res_list = []
        dt_list = fd.tradingday(start_time, end_time)
        groups_limit = 100
        groups = len(dt_list) // groups_limit
        groups = 1 if groups == 0 else groups
        dt_groups = []
        for i in range(groups):
            if i != groups - 1:
                dt_groups.append((dt_list[i * groups_limit], dt_list[(i + 1) * groups_limit - 1]))
            else:
                dt_groups.append((dt_list[i * groups_limit], dt_list[-1]))
        for i in trange(len(dt_groups)):
            s, e = dt_groups[i]
            start_time = s[:4] + "." + s[4:6] + "." + s[6:]
            end_time = e[:4] + "." + e[4:6] + "." + e[6:]
            temp = self.s.run(
                f"load_data_from_dfs_remote({symbol},{factor_list},{start_time}, {end_time},'{factor_type}', '{data_type}',\
             'public')")
            res_list.append(temp)
        res = pd.concat(res_list)
        return res

    # 读取因子库因子列表
    def load_info_from_dfs(self, factor_type, source_type, data_type='enhanced_tick', factors=[]):
        """

        :param factors:
        :param data_type: enhanced_tick and  trade
        :param factor_type: str类型。两个可选项为'factor' or 'label'，分别表示查询因子表、标签表
        :param source_type: str类型。两个可选项为'personal' or 'public'，分别表示个人库、公共库
        :return:
        """
        self.s.run("""use DolphinFrame::FactorProvider""")
        if type(factors) != list:
            raise Exception("[FactorProvider]入参factors必须是list格式")
        if len(factors) == 0:
            factors = 'NULL'

        res = self.s.run(
            f"DolphinFrame::FactorProvider::get_info_from_dfs_remote('{factor_type}', '{data_type}', '{source_type}',\
            `{self.userID},{factors})")
        return res

    def online_factor_to_dfs(self, factor_type, factor_list, file_path):
        """
        :param factor_type:
        :param factor_list:
        :param file_path:
        :return:
        """
        # TODO:权限校验
        if factor_type not in ['factor', 'label']:
            raise Exception("factor_type 不符合要求 仅支持 factor 和 label两种")
        else:
            if factor_type == 'factor':
                target_path = self.online_factor_path
            else:
                target_path = self.online_label_path

        for factor_name in factor_list:
            factor_file_name = os.path.join(file_path, factor_name + ".dos")
            if os.path.exists(factor_file_name):
                raise Exception("未找到符合要求的因子。 {}".format(factor_file_name))
            os.system("rsync --chmod=Fo+rw -avz {}  {}".format(factor_file_name, target_path))
        self.s.run("""use DolphinFrame::FactorProvider
        FactorProvider::online_factor_to_dfs({},{},'{}', '{}')
        """.format(factor_list, target_path, factor_type, self.userID))

    def offline_factor_from_dfs(self, factor_list, factor_type):
        # TODO：权限校验

        self.s.run("""use DolphinFrame::FactorProvider
        FactorProvider::offline_factor_from_dfs_remote({},'{}','{}')
        """.format(factor_list, factor_type, self.userID))
        return

    def __get_market_data(self, stock=None, startTime=None, endTime=None, tableName=None, fields=None):
        """

        :param stock: list类型，单标的支持string
        :param startTime: str类型，格式YYYYMMDD，如20220601
        :param endTime: str类型，格式YYYYMMDD，如20220601
        :param tableName: string类型。可查询表如下
        :return:
        """
        if isinstance(startTime, int):
            startTime = str(startTime)
        if isinstance(endTime, int):
            endTime = str(endTime)
        check_date(startTime)
        check_date(endTime)
        startTime = startTime[:4] + '.' + startTime[4:6] + '.' + startTime[6:]
        endTime = endTime[:4] + '.' + endTime[4:6] + '.' + endTime[6:]
        if isinstance(stock, str):
            stock = [stock]
        if not stock:
            stock = 'NULL'
        if not fields:
            fields = 'NULL'
        else:
            if isinstance(fields, str):
                fields = [fields]

        self.s.run("use DolphinFrame::DataManager")
        self.s.run(
            f"""data = getMarketData_Remote(stock={stock}, startTime={startTime}, endTime={endTime}, tableName=`{tableName}, fields={fields})""")

        # arrayVector_columns = self.s.run("select name from data.schema().colDefs where typeString like '%[]'")
        # for col in arrayVector_columns.name:
        #     self.s.run(f"data.replaceColumn!(`{col}, string(data.{col}))")
        data = self.s.run("data")
        # for col in arrayVector_columns.name:
        #    data[col] = data[col].apply(lambda x: eval(x))

        time_columns = self.s.run("select name from data.schema().colDefs where typeString=`TIME")
        for col in time_columns.name:
            data[col] = data[col].apply(lambda x: x.time())
        return data

    def get_market_data(self, stock=None, startTime=None, endTime=None, tableName=None, exchange=None,
                        securityType=None,
                        marketType=None, is_real=False, fields=None):
        """
        原始行情、扩充行情取数接口
        表名入参有两种方式：
        1.直接入参tableName，无需入参exchange、securityType、marketType
        2.不入参tableName，需入参exchange、securityType、marketType
        :param stock: list类型，单标的支持string,不传的话默认取全部标的
        :param startTime: str类型，格式YYYYMMDD，如20220601
        :param endTime: str类型，格式YYYYMMDD，如20220601
        :param tableName: string类型。可查询表如下
        :param exchange: str，交易所。可选项'sh','sz'
        :param securityType: str，证券类型。可选项'stock','bond'
        :param marketType: str，数据类型。可选项'order'-逐笔委托；'trade'-逐笔成交，'trade_order'-还原逐笔；'tick'-3stick，
                                         'tick_enhanced'-增强3stick；'trade_enhanced'-增强trade；'tick_persec'-秒级tick,'tick_l2p'- level2Plus
        :return:
        """
        """
        可查询表：
        深交所股票逐笔成交数据	sz_stock_trade
        深交所股票逐笔委托数据	sz_stock_order
        深交所股票还原逐笔数据	sz_stock_trade_order
        上交所股票逐笔成交数据	sh_stock_trade
        上交所股票逐笔委托数据	sh_stock_order
        深交所转债逐笔成交数据	sz_bond_trade
        深交所转债逐笔委托数据	sz_bond_order
        深交所转债还原逐笔数据	sz_bond_trade_order
        上交所转债逐笔委托数据	sh_bond_order
        上交所转债逐笔成交数据	sh_bond_trade
        上交所转债还原逐笔数据	sh_bond_trade_order
        深交所股票秒级tick数据	sz_stock_tick_persec
        深交所转债秒级tick数据	sz_bond_tick_persec
        上交所股票增强tick数据	sh_stock_tick_enhanced
        深交所股票增强trade数据	sz_stock_tick_enhanced
        上交所股票增强trade数据	sh_stock_trade_enhanced
        上交所股票原始tick数据	sh_stock_tick
        """
        fd = FactorData()
        data_list = []
        if tableName:
            dt_list = fd.tradingday(startTime, endTime)
            groups_limit = 100
            groups = len(dt_list) // groups_limit
            groups = 1 if groups == 0 else groups
            dt_groups = []
            for i in range(groups):
                if i != groups - 1:
                    dt_groups.append((dt_list[i * groups_limit], dt_list[(i + 1) * groups_limit - 1]))
            else:
                dt_groups.append((dt_list[i * groups_limit], dt_list[-1]))
            for i in trange(len(dt_groups)):
                s, e = dt_groups[i]
                try:
                    temp = self.__get_market_data(stock, s, e, tableName, fields=fields)
                except:
                    temp = pd.DataFrame()
                data_list.append(temp)
        elif exchange and securityType and marketType:
            if is_real:
                tableName = "real_" + exchange + '_' + securityType + '_' + marketType
            else:
                tableName = exchange + '_' + securityType + '_' + marketType
            dt_list = fd.tradingday(startTime, endTime)
            groups_limit = 100
            groups = len(dt_list) // groups_limit
            groups = 1 if groups == 0 else groups
            dt_groups = []
            for i in range(groups):
                if i != groups - 1:
                    dt_groups.append((dt_list[i * groups_limit], dt_list[(i + 1) * groups_limit - 1]))
            else:
                dt_groups.append((dt_list[i * groups_limit], dt_list[-1]))
            for i in trange(len(dt_groups)):
                s, e = dt_groups[i]
                try:
                    temp = self.__get_market_data(stock, s, e, tableName, fields=fields)
                except:
                    temp = pd.DataFrame()
                data_list.append(temp)

        else:
            raise Exception("""表入参支持两种形式：
                                1.只传表名tableName；
                                2.表名组合，即exchange、securityType、marketType""")
        return pd.concat(data_list)

    # 从数据库中获取因子入库流程状态
    def load_record(self, factor_name=None, status=None):
        self.s.run(f"""use DolphinFrame::FactorProvider""")
        if factor_name:
            if isinstance(factor_name, str):
                factor_name = [factor_name]
            if not status:
                res = self.s.run(
                    f"""select * from loadTable("dfs://PublicData/commondata/EhnancedTick", `factor_status) where factorName in {factor_name}""")
            else:
                res = self.s.run(
                    f"""select * from loadTable("dfs://PublicData/commondata/EhnancedTick", `factor_status) where factorName in {factor_name}, status = {status}""")
        else:
            if status:
                res = self.s.run(
                    f"""select * from loadTable("dfs://PublicData/commondata/EhnancedTick", `factor_status) where status = {status}""")
            else:
                res = self.s.run(
                    f"""select * from loadTable("dfs://PublicData/commondata/EhnancedTick", `factor_status)""")
        del res['id']
        return res

    def research_data_check(self, stocks, data_type='enhanced_tick_norm', detail=False, factor_list=None,
                            label_list=None, check_start_date='20220101'):
        import datetime
        dol_start_date = check_start_date[:4] + "." + check_start_date[4:6] + "." + check_start_date[6:]
        cur_date = datetime.datetime.now().strftime("%Y%m%d")
        parse_date = fd.tradingday(cur_date, -2)[0]
        if not isinstance(stocks, list):
            raise Exception("[FactorManager]必须传入待检查的标的列表")
        self.s.run(f"""use DolphinFrame::FactorProvider""")

        md_res = self.s.run(f"""
            md_res,factor_res,label_res = research_data_check_remote({stocks}, '{data_type}', '{self.userID}',{dol_start_date})
            md_res
        """)
        md_res['mddate'] = md_res['mddate'].apply(lambda x: str(x)[:10])

        factor_res = self.s.run(f"""factor_res""")
        label_res = self.s.run(f"""label_res""")
        if data_type == 'enhanced_tick_norm':
            factor_res['stock'] = factor_res['stock'].apply(lambda x: x[:-2] + "." + x[-2:])
            label_res['stock'] = label_res['stock'].apply(lambda x: x[:-2] + "." + x[-2:])
        factor_res['mddate'] = factor_res['mddate'].apply(lambda x: str(x)[:10])
        label_res['mddate'] = label_res['mddate'].apply(lambda x: str(x)[:10])
        # 按票返回结果
        res_stocks = {}
        for stock in stocks:
            md_res_per_stock = md_res[md_res['stock'] == stock]
            if md_res_per_stock.shape[0] == 0:
                print("[FactorCheck] 标的：{} 暂无行情数据".format(stock))
            factor_res_per_stock = factor_res[factor_res['stock'] == stock]
            if factor_res_per_stock.shape[0] == 0:
                print("[FactorCheck] 标的：{} 暂无因子数据".format(stock))
            label_res_per_stock = label_res[label_res['stock'] == stock]
            if label_res_per_stock.shape[0] == 0:
                print("[FactorCheck] 标的：{} 暂无标签数据".format(stock))

            listing_date = str(
                fd.get_factor_value("Basic_factor", [stock], [parse_date], ['listing_date'])["listing_date"].iloc[0])
            date_list = fd.tradingday(max(listing_date, check_start_date), cur_date)
            md_date_list = [str(i).replace("-", "") for i in sorted(list(set(md_res_per_stock['mddate'].values)))]
            md_lack_date_list = sorted(list(set(date_list) - set(md_date_list)))
            # 因子和标签取的都是交集
            factor_date_list = [str(i).replace("-", "") for i in
                                sorted(list(set(factor_res_per_stock['mddate'].values)))]
            label_date_list = [str(i).replace("-", "") for i in sorted(list(set(label_res_per_stock['mddate'].values)))]
            factor_lack_date_list = sorted(list(set(date_list) - set(factor_date_list)))
            label_lack_date_list = sorted(list(set(date_list) - set(label_date_list)))
            res_stocks[stock] = {}
            res_stocks[stock]['md_info'] = md_lack_date_list
            res_stocks[stock]['factor_info'] = factor_lack_date_list
            res_stocks[stock]['label_info'] = label_lack_date_list
            if detail:
                if not isinstance(factor_list, list) or not isinstance(label_list, list):
                    raise Exception("[FactorCheck] 需要更详细的数据的话，需要传入因子和标签列表")
                res_stocks[stock]['factor_info_detail'] = []
                res_stocks[stock]['label_info_detail'] = []
                for factor in factor_list:
                    factor_res_per_stock_per_fac = factor_res_per_stock[factor_res_per_stock['factor_name'] == factor]
                    factor_date_list_per_fac = [str(i).replace("-", "") for i in
                                                sorted(list(set(factor_res_per_stock_per_fac['mddate'].values)))]
                    factor_lack_date_list_per_fac = {
                        factor: sorted(list(set(date_list) - set(factor_date_list_per_fac)))}
                    res_stocks[stock]['factor_info_detail'].append(factor_lack_date_list_per_fac)
                for label in label_list:
                    label_res_per_stock_per_fac = label_res_per_stock[label_res_per_stock['factor_name'] == label]
                    label_date_list_per_fac = [str(i).replace("-", "") for i in
                                               sorted(list(set(label_res_per_stock_per_fac['mddate'].values)))]
                    label_lack_date_list_per_fac = {label: sorted(list(set(date_list) - set(label_date_list_per_fac)))}
                    res_stocks[stock]['label_info_detail'].append(label_lack_date_list_per_fac)
        return res_stocks


if __name__ == "__main__":
    import pandas as pd

    pd.set_option('display.max_columns', 100)
    pd.set_option('display.max_rows', 300)
    # 调整显示宽度，以便整行显示
    pd.set_option('display.width', 1000)

    fd = FactorProvider(userID="K0321499")
    # fd.create_database_table(reCreateDB=False, reCreateFactorTB=False, reCreateLabelTB=False)  # 请确认参数！请确认参数！请确认参数！
    # import pandas as pd
    #
    # res = pd.read_parquet("res.parquet")
    # print(res)

    # 保存因子或标签
    # res = None  # 这里是为把旧表数据同步到新表临时设置
    # factor_type = 'factor'
    # res = fd.save_personal_data_to_dfs(res, factor_type)

    # factor_list = ['labelEQtriplebarriertaggertypeEQmidpricedsizeEQ300']
    # res = fd.load_personal_data_from_dfs(symbol='688363.SH', factor_list=factor_list, start_time='20220610',
    #                                      end_time='20220610', factor_type='label')
    # print(res)

    # res = fd.load_public_data_from_dfs(symbol='688363.SH', factor_list=factor_list, start_time='20220610',
    #                                      end_time='20220610', factor_type='label')
    # print(res)

    # 获取因子或标签列表
    # res = fd.load_info_from_dfs(factor_type='factor', source_type='personal')
    # print(res)

    # 原始行情、扩充行情取数接口
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", tableName="sh_stock_tick")  # 原始tick
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", tableName="sh_stock_trade")  # 原始trade
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", tableName="sh_stock_tick_enhanced")  # 增强tick

    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", exchange='sh', securityType='stock', marketType='tick')  # 原始tick
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", exchange='sh', securityType='stock', marketType='trade')  # 原始trade
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", exchange='sh', securityType='stock', marketType='tick_enhanced') # 增强tick
    # print(data)

    analysis_df = '/tmp/pycharm_project_609/DolphinDB/automininghff/AutoMiningFrame/DataCaculation/entry/analysis_res.pkl'
    analysis_res = pd.read_pickle(analysis_df)
    fd.upload_factor_analysis_res(analysis_res, table_type='personal')
