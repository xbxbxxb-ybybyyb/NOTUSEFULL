import pickle
from SparkUtils.FileDumpHbaseUtils.SparkLauncher import SparkLauncher
from SparkUtils.FileDumpHbaseUtils.TaskMeta import TaskMeta
from HFDataLoader.DumpTickFileHbase import get_codeDateDict_HDFS

def main(marketDataLibrary, hdfsPath, codeDateDict, hbase, env):

    taskList = []

    for code, dateList in codeDateDict.items():
        taskList.append(
            TaskMeta( marketDataLibrary,
                      hdfsPath,
                      code,
                      dateList,
                      hbase,
                      env)
        )

    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch()


if __name__ == "__main__":
    marketDataLibrary = "XHFDataLib"
    hdfsPath = "HFDataDump/T"
    hbase = False
    env = "Spark"

    codeDateDict = get_codeDateDict_HDFS(hdfs_path=hdfsPath, save=False)
    # with open('/data/user/015629/MISC/codeDateDict.pkl', 'rb') as f:
    #     codeDateDict = pickle.load(f)

    main(marketDataLibrary, hdfsPath, codeDateDict, hbase, env)
