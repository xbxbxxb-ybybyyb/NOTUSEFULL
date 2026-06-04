# Updated on 2018/7/16 by 010022 -- 改造以支持取跨日数据+并行化运算
# Updated on 2018/7/17 by 006566 -- 若个股某日无交易，将股票代码和日期打印出来

# -*- coding: utf-8 -*-
import datetime as dt
import os
from os import path
import random
import sys
import io
import time
import zipfile
import pickle
import socket
import grpc
import configparser
from pyspark import SparkContext, SparkConf
from concurrent import futures
from pyarrow import hdfs
from System.StrategyBase import StrategyBase
from System.StrategyMeta import StrategyMeta
from System.TaskMeta import TaskMeta
from System.MergeMeta import MergeMeta
from System.Utils import parseDate, randomFileName
from System import Func
from Rpc import RpcService_pb2_grpc
from System.RpcServer import QuantFactorServicer
from System.GetValidTradingDay import getValidTradingDayList


class StrategyManagement:
    def __init__(self):
        self.__MAX_EXECUTOR_TASK_NUM = 200
        self.__MAX_EXECUTOR_INSTANCES = 500
        self.__config = configparser.ConfigParser()
        self.__config.read('/home/appadmin/.config/octopus/quantfactor.ini')
        self.__strategy = []
        self.__strategyMetas = []
        self.__tradeDatesFile = self.__config['quantfactor']['trade.dates.file']
        self.__srcDir = self.__config['quantfactor']['data.source.dir']
        self.__dstDir = ""
        # 用来临时存储每个Executor的python运行环境依赖
        self.__tmpEnvDir = path.join('/tmp', 'quantfactor', randomFileName())
        self.__daysInterval = int(self.__config['quantfactor']['days.interval'])
        self.__func = Func.execute
        self.__sc = None
        self.__dfs = None
        os.environ['JAVA_HOME'] = self.__config['hadoop']['java.home']
        os.environ['JAVA_TOOL_OPTIONS'] = '-Xss1280K'
        os.environ['ARROW_LIBHDFS_DIR'] = self.__config['hadoop']['libhdfs.dir']
        os.environ['PYSPARK_PYTHON'] = self.__config['spark']['spark.pyspark.python']
        os.environ['HADOOP_HOME'] = self.__config['hadoop']['hadoop.home']
        os.environ['HADOOP_CONF_DIR'] = self.__config['hadoop']['hadoop.conf.dir']
        os.environ['YARN_CONF_DIR'] = self.__config['yarn']['yarn.conf.dir']
        os.environ['HADOOP_USER_NAME'] = self.__config['hadoop']['hadoop.user.name']
        # 用于在Driver端绑定RPC服务
        self.__rpcHost = self.__config['quantfactor']['driver.hostname']
        self.__rpcPort = getFreePort(self.__rpcHost)
        self.__rpcServer = None
        self.__strategyNames = set()
        
    def setDstDir(self, dstDir):
        self.__dstDir = dstDir

    def getDstDir(self):
        return self.__dstDir

    def setFunc(self, func):
        self.__func = func

    def setDaysInterval(self, daysInterval):
        self.__daysInterval = daysInterval

    def registerStrategy(self, strategy):
        # 将策略注册到策略管理模块
        if strategy in self.__strategy or strategy.getStrategyName() in self.__strategyNames:
            raise Exception('Strategy {} already exists'.format(strategy.getStrategyName()))
        elif strategy.getStrategyName() == '':
            raise Exception('Strategy name not set')
        elif ' ' in strategy.getStrategyName():
            raise Exception('Strategy name {} contains white space'.format(strategy.getStrategyName()))
        else:
            self.__strategy.append(strategy)
            self.__strategyMetas.append(StrategyMeta(strategy))
            self.__strategyNames.add(strategy.getStrategyName())

    def getStrategy(self):
        return self.__strategy

    def start(self):
        startTimeStamp = dt.datetime.timestamp(dt.datetime.now())
        self.__checkConditions()
        self.__initEnv()
        self.__startRpc()
        taskMetas = self.__splitTasks()
        try:
            self.__runTasks(taskMetas)
            self.__mergeOutput()
        finally:
            try:
                self.__clearHDFSTmpDir()
            finally:
                self.__clearTmpEnvDir()
        endTimeStamp = dt.datetime.timestamp(dt.datetime.now())
        print("Calculating time: " + str(round((endTimeStamp - startTimeStamp) / 60, 2)) + " min")

    def __initEnv(self):
        self.__dfs = hdfs.connect()
        if not self.__dfs.exists(self.__srcDir):
            raise Exception("Source directory {} doesn't exist".format(self.__srcDir))
        if self.__dfs.exists(self.__dstDir):
            raise Exception("Destination directory {} already exist".format(self.__dstDir))
        tmpDir = path.join(self.__dstDir, '.tmp')
        self.__dfs.mkdir(tmpDir)
        self.__dfs.chmod(self.__dstDir, 0o777)
        self.__dfs.chmod(tmpDir, 0o777)
        zipStr = zipPythonFiles()
        with self.__dfs.open(path.join(tmpDir, 'sources.zip'), 'wb') as f:
            f.write(zipStr)
        sparkConf = SparkConf().setAppName("QuantFactor").setMaster("yarn")
        for key in self.__config['spark']:
            sparkConf.set(key, self.__config["spark"][key])
        sparkConf.set('spark.executor.memory', '6g')
        sparkConf.set('spark.executor.instances', str(self.__MAX_EXECUTOR_INSTANCES))
        sparkConf.set('spark.driver.memory', '100g')
        self.__sc = SparkContext(conf=sparkConf)

    def __startRpc(self):
        # 这个rpcServer一定一定不能用局部变量, 否则一旦这个方法返回, 这个对象会被gc掉, 从而RPC服务就结束了
        # 别问我是怎么知道的, 血的教训.......................................
        self.__rpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        RpcService_pb2_grpc.add_QuantFactorServicer_to_server(QuantFactorServicer(), self.__rpcServer)
        self.__rpcServer.add_insecure_port('{}:{}'.format(self.__rpcHost, self.__rpcPort))
        self.__rpcServer.start()

    def __splitTasks(self):
        taskMetas = []
        for i in range(self.__strategy.__len__()):
            taskMetas.extend(self.__splitStrategy(i))
        return taskMetas

    def __splitStrategy(self, strategyIndex):
        taskMetas = []
        strategy = self.__strategy[strategyIndex]
        daysList = self.__splitDays(strategy)
        self.__strategyMetas[strategyIndex].setDaysList(daysList)
        codeGroups = strategy.getTradingUnderlyingCode()
        for i in range(codeGroups.__len__()):
            for j in range(daysList[i].__len__()):
                strategyBase = StrategyBase(strategy)
                taskMeta = TaskMeta(strategyBase, strategyIndex, i, daysList[i][j], j)
                taskMetas.append(taskMeta)
        return taskMetas

    def __splitDays(self, strategy):
        allSplitDays = []
        codeGroups = strategy.getTradingUnderlyingCode()
        startDate = parseDate(strategy.getStartDateTime())
        endDate = parseDate(strategy.getEndDateTime())
        for i in range(codeGroups.__len__()):
            tradeDatesDT = getValidTradingDayList(codeGroups[i][0], startDate, endDate, True)
            datesStr = []
            for j in range(tradeDatesDT.__len__()):
                datestr = dt.datetime.strftime(tradeDatesDT[j], '%Y/%m/%d')
                datesStr.append(datestr)
            splitDays = []
            offset = 0
            # 切片时为了取到前一天的数据,切片都会多拿一天的数据, 第一天的数据不会播放,用来计算第二天开盘的因子
            while offset < datesStr.__len__() - 1:
                splitDays.append(datesStr[offset:offset + self.__daysInterval + 1])
                offset += self.__daysInterval
            allSplitDays.append(splitDays)

        return allSplitDays

    def __runTasks(self, taskMetas):
        # 这里一定要将taskmeta序列化再传进RDD, 因为Executor端的依赖是在后面的foreachpartition中动态加载的, 而在这之前Executor无法实例化TaskMeta
        executor_task_num  = self.__MAX_EXECUTOR_TASK_NUM
        executor_instances = self.__MAX_EXECUTOR_INSTANCES
        pickledTaskMetas = [pickle.dumps(t) for t in taskMetas]
        task_num = len(pickledTaskMetas)
        partition_num = max(task_num // executor_task_num, min(executor_instances, task_num))
        rdd = self.__sc.parallelize(pickledTaskMetas, partition_num)
        f = makeTaskFunc(os.environ['JAVA_HOME'], os.environ['HADOOP_HOME'], os.environ['ARROW_LIBHDFS_DIR'],
                         self.__func, self.__srcDir, self.__dstDir, self.__tmpEnvDir, self.__rpcHost, self.__rpcPort)
        rdd.foreachPartition(f)

    def __mergeOutput(self):
        mergeMetas = []
        for i in range(self.__strategy.__len__()):
            for j in range(self.__strategy[i].getTradingUnderlyingCode().__len__()):
                numIntervals = self.__strategyMetas[i].getNumIntervals(j)
                meta = MergeMeta(StrategyBase(self.__strategy[i]), i, j, numIntervals)
                mergeMetas.append(meta)
        # 这里一定要将mergemeta序列化再传进RDD, 因为Executor端的依赖是在后面的foreachpartition中动态加载的, 而在这之前Executor无法实例化MergeMeta
        pickledMergeMetas = [pickle.dumps(m) for m in mergeMetas]
        rdd = self.__sc.parallelize(pickledMergeMetas, len(pickledMergeMetas))
        f = makeMergeFunc(os.environ['JAVA_HOME'], os.environ['HADOOP_HOME'], os.environ['ARROW_LIBHDFS_DIR'],
                          self.__dstDir, self.__tmpEnvDir)
        rdd.foreachPartition(f)

    def __clearHDFSTmpDir(self):
        self.__dfs.rm(path.join(self.__dstDir, '.tmp'), recursive=True)

    def __clearTmpEnvDir(self):
        """
        将所有Executor上的存储环境依赖的临时目录删除
        """
        # 构造一个大的rdd, 确保每个Executor上都有其partition
        rdd = self.__sc.parallelize(range(10000))
        f = makeCleanupFunc(self.__tmpEnvDir)
        rdd.foreachPartition(f)

    def __checkConditions(self):
        if self.__dstDir == "":
            raise Exception('Destination directory not set')
        if self.__daysInterval <= 0:
            raise Exception('Illegal days interval %d' % self.__daysInterval)
        if not self.__func:
            raise Exception('UDF not set')


def getFreePort(host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def zipPythonFiles():
    # 获取该工程的根目录, 将该目录下的Factor, NonFactor, System, Tag, Rpc目录下的所有python文件打进压缩包
    # 后续如果需要添加其他依赖，需要修改该方法，并且更新getEnvFunctions#prepareEnv()方法
    projectDir = path.dirname(path.dirname(path.abspath(__file__)))
    writer = io.BytesIO()
    with zipfile.ZipFile(writer, 'w', zipfile.ZIP_DEFLATED) as ziph:
        for subDir in ['Factor', 'NonFactor', 'System', 'Tag', 'Rpc']:
            for f in os.listdir(path.join(projectDir, subDir)):
                if len(f) > 3 and f[-3:] == '.py':
                    ziph.write(path.join(projectDir, subDir, f), arcname=path.join(subDir, f))
    return writer.getvalue()


def makeTaskFunc(javaHome, hadoopHome, libhdfsDir, func, srcDir, dstDir, tmpEnvDir, rpcHost, rpcPort):
    # 必须用这种嵌套函数的方式，否则pyspark无法序列化
    isEnvReady, prepareEnv, resetClasspath = getEnvFunctions()
    # 该UDF函数会依赖工程中的python文件，如果不先序列化，而是直接传进去，因为Executor端的依赖环境是动态加载的，
    # 会导致Spark无法在Executor端反序列化该函数
    pickledFunc = pickle.dumps(func)

    def f(it):
        os.environ['JAVA_HOME'] = javaHome
        os.environ['JAVA_TOOL_OPTIONS'] = '-Xss1280K'
        os.environ['ARROW_LIBHDFS_DIR'] = libhdfsDir
        os.environ['HADOOP_HOME'] = hadoopHome
        # 这里将CLASSPATH重置, 否则因为yarn已经初始化了该变量, 导致下面的hdfs.connect()报错（错误原因未知）
        resetClasspath()
        dfs = hdfs.connect()
        if not isEnvReady():
            prepareEnv(dfs, dstDir, tmpEnvDir)
        srcDir0 = srcDir  # 保存srcDir的引用, 因为Worker.work方法是采用exec调用的, 如果不保存, 序列化后的f方法将不会有这个变量
        if 'RPC_DRIVER_HOST' not in os.environ:
            os.environ['RPC_DRIVER_HOST'] = rpcHost
        if 'RPC_DRIVER_PORT' not in os.environ:
            os.environ['RPC_DRIVER_PORT'] = str(rpcPort)
        func0 = pickle.loads(pickledFunc)
        # 下面两处必须写程exec的形式，因为在Spark Executor在执行f方法之前，依赖环境还未加载，如果直接写成普通形式，会导致Executor无法
        # 反序列化该f方法
        exec('import Worker')
        for pickledTaskMeta in it:
            taskMeta = pickle.loads(pickledTaskMeta)
            exec('Worker.work(dfs, taskMeta, func0, srcDir0, dstDir)')

    return f


def makeMergeFunc(javaHome, hadoopHome, libhdfsDir, dstDir, tmpEnvDir):
    isEnvReady, prepareEnv, resetClasspath = getEnvFunctions()

    def f(it):
        os.environ['JAVA_HOME'] = javaHome
        os.environ['JAVA_TOOL_OPTIONS'] = '-Xss1280K'
        os.environ['ARROW_LIBHDFS_DIR'] = libhdfsDir
        os.environ['HADOOP_HOME'] = hadoopHome
        # 这里将CLASSPATH重置, 否则因为yarn已经初始化了该变量, 导致下面的hdfs.connect()报错（错误原因未知）
        resetClasspath()
        dfs = hdfs.connect()
        if not isEnvReady():
            prepareEnv(dfs, dstDir, tmpEnvDir)
        exec('import Worker')
        for pickledMergeMeta in it:
            mergeMeta = pickle.loads(pickledMergeMeta)
            exec('Worker.merge(dfs, dstDir, mergeMeta)')

    return f


def getEnvFunctions():
    # 该函数定义不能放在外层, 否则pyspark序列化该方法时只会保存它的引用, 从而导致Executor端无法实例化该方法
    def isEnvReady():
        try:
            import System, Factor, NonFactor, Tag
        except ImportError:
            # 无法加载这些模块, 说明Executor环境未初始化
            return False
        return True

    # 该函数定义不能放在外层, 否则pyspark序列化该方法时只会保存它的引用, 从而导致Executor端无法实例化该方法
    def prepareEnv(dfs, dstDir, tmpEnvDir):
        # 保证线程安全
        threadRandom = random.Random()
        threadRandom.seed(time.time())
        localTmpDir = path.join(tmpEnvDir, str(threadRandom.randint(0, sys.maxsize)))
        os.makedirs(localTmpDir)
        with dfs.open(path.join(dstDir, '.tmp', 'sources.zip'), 'rb') as reader:
            zipStr = reader.read()
            f = io.BytesIO(zipStr)
            with zipfile.ZipFile(f, 'r') as ziph:
                ziph.extractall(localTmpDir)
        sys.path.append(localTmpDir)
        sys.path.append(path.join(localTmpDir, 'Factor'))
        sys.path.append(path.join(localTmpDir, 'NonFactor'))
        sys.path.append(path.join(localTmpDir, 'System'))
        sys.path.append(path.join(localTmpDir, 'Tag'))
        sys.path.append(path.join(localTmpDir, 'Rpc'))

    # 该函数定义不能放在外层, 否则pyspark序列化该方法时只会保存它的引用, 从而导致Executor端无法实例化该方法
    def resetClasspath():
        import subprocess
        hadoopBin = '{}/bin/hadoop'.format(os.environ['HADOOP_HOME'])
        classpath = subprocess.check_output([hadoopBin, 'classpath', '--glob'])
        os.environ['CLASSPATH'] = classpath.decode('utf-8')

    return isEnvReady, prepareEnv, resetClasspath


def makeCleanupFunc(tmpEnvDir):
    def f(it):
        from os import path
        if path.exists(tmpEnvDir):
            import shutil
            shutil.rmtree(tmpEnvDir, ignore_errors=True)  # 由于在多线程环境下可能会导致重复删除, 这里忽略错误

    return f
