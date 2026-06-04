[spark]
spark.executor.instances = 600
spark.executor.cores = 1
spark.executor.memory = 4g
spark.python.worker.memory = 4g
spark.yarn.executor.memory = 4g
spark.yarn.queue=root.app.xquant.StrategyTrading
#spark.yarn.queue=user
spark.pyspark.python = /usr/lib/anaconda3/bin/python3
spark.driver.memory = 4g
spark.python.worker.reuse=false
spark.yarn.keytab=/opt/anaconda3/lib/python3.6/site-packages/QuantFramework/conf/xquant.keytab
spark.yarn.principal=xquant

[hadoop]
java.home = /usr/java/jdk1.8.0_144
hadoop.home = /opt/cloudera/parcels/CDH/lib/hadoop/
hadoop.conf.dir = /etc/hadoop/conf
hadoop.user.name = xquant
libhdfs.dir = /opt/cloudera/parcels/CDH-5.13.0-1.cdh5.13.0.p0.29/lib64


[yarn]
yarn.conf.dir = /etc/hadoop/conf

[quantfactor]
# 启动程序所在节点的主机名或ip地址
driver.hostname = 168.9.64.62
# 任务日期切分粒度
days.interval = 1
# 交易日列表文件在HDFS中的路径
trade.dates.file = /htdata/mdc/stockData/TradeDates.txt
# 数据源在HDFS中的目录
data.source.dir = /htdata/mdc/MDStockData
