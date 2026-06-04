#!/bin/bash
export JAVA_HOME=/home/appadmin/jdk1.8.0_162
export CLASSPATH=$JAVA_HOME/lib:$JAVA_HOME/jre/lib
export PYTHON_HOME=/home/appadmin/Python-3.6.8
export ANACONDA_HOME=/home/appadmin/anaconda3
export PYTHON_EXEC_ENV=ats-quant
export PATH=$ANACONDA_HOME/bin:$PYTHON_HOME/bin:$JAVA_HOME/bin:$JAVA_HOME/jre/bin:$PATH
export PREFIX_IP=168

IFCFG=$(whereis -b ifconfig | awk '{print $2}')

AMI_HOME_PATH=/home/appadmin/AMI
export LD_LIBRARY_PATH=${AMI_HOME_PATH}/lib64:${AMI_HOME_PATH}/lib64/jni/:${AMI_HOME_PATH}/lib64/connector/:/lib64:$LD_LIBRARY_PATH
export ETCD_PATH=${AMI_HOME_PATH}
export ETCDCTL_API=3
export AMI_HOME=$AMI_HOME_PATH

function heapsizegb() { 
    ratio=$1;
    read -r _ freemem _ <<< "$(grep --fixed-strings 'MemTotal' /proc/meminfo)"
    bc <<< "scale=0;(${freemem}/1024/1024*${ratio})/1"
}

function heapsizemb() { 
    ratio=$1;
    read -r _ freemem _ <<< "$(grep --fixed-strings 'MemTotal' /proc/meminfo)"
    bc <<< "scale=0;(${freemem}/1024*${ratio})/1"
}

function getip() {
    local EXCLUDE_IP=$($IFCFG -a | grep inet -B1 | grep -A1 virbr0 | grep inet | awk '{print $2}' | tr -d "addr:" | tr -d '\r')
    local DOCKER_IP=$($IFCFG -a | grep inet -B1 | grep -A1 docker0 | grep inet | awk '{print $2}' | tr -d "addr:" | tr -d '\r')
    if [ ! -z $DOCKER_IP ];then
        DOCKER_IP=172.17.0.1
    fi
    if [ ! -z $EXCLUDE_IP ];then
        echo $($IFCFG -a | grep inet | grep -v $EXCLUDE_IP |grep -v $DOCKER_IP | grep -v 127.0.0.1 | grep -v inet6 |grep $PREFIX_IP| awk '{print $2}' | tr -d "addr:")
    else
        echo $($IFCFG -a | grep inet |grep -v $DOCKER_IP |grep -v 127.0.0.1 | grep -v inet6 |grep $PREFIX_IP|  awk '{print $2}' | tr -d "addr:")
    fi  
}

LOCAL_IP=$(getip)

GC_LOG_FILE=log/gc.log.${LOCAL_IP}.$(date +%Y-%m-%d-%H-%M)

GC_LOG_CONTENT_ARGS="-Xloggc:${GC_LOG_FILE} \
-verbose:gc \
-XX:+PrintGC \
-XX:+PrintGCDetails \
-XX:+PrintGCApplicationStoppedTime \
-XX:+PrintHeapAtGC \
-XX:+PrintGCDateStamps \
-XX:+PrintAdaptiveSizePolicy \
-XX:+PrintTenuringDistribution \
-XX:PrintFLSStatistics=1 "

GC_ARGS="-XX:+UseG1GC \
-XX:+ParallelRefProcEnabled \
-XX:MaxGCPauseMillis=400 \
-XX:MetaspaceSize=512m \
-XX:+UseStringDeduplication "

function startup_application {
BASEDIR=$(cd `dirname $0`; pwd)
MAIN=$1
CONFIG=$2
SYSTEM=$3

create_log_directory
get_delimiter
import_extension

HEAP_SIZE=$(heapsizegb 0.6)

java -server  -d64 -Xms${HEAP_SIZE}G -Xmx${HEAP_SIZE}G \
-XX:+UseG1GC \
-XX:+ParallelRefProcEnabled \
-Xloggc:log/gc.log.$(date +%Y-%m-%d-%H-%M) \
-XX:MaxGCPauseMillis=400 \
-XX:+PrintGCDateStamps \
-XX:+PrintHeapAtGC \
-XX:+HeapDumpOnOutOfMemoryError \
-XX:HeapDumpPath=log/gcdump \
-Doctopus.conf="${BASEDIR}/conf/profile/collector.properties" \
-Dcom.sun.management.jmxremote.port=9999 \
-Dcom.sun.management.jmxremote.ssl=false \
-Dcom.sun.management.jmxremote.authenticate=false \
-cp "${BASEDIR}/bin/*${DELIMITER}${BASEDIR}/lib/*${DELIMITER}${BASEDIR}/conf/*${DELIMITER}${BASEDIR}/conf/common/*${DELIMITER}${BASEDIR}/strategy/*${DELIMITER}" \
-Dlocation="${BASEDIR}" -Dlog4j.configurationFile="conf/profile/log4j2.xml" \
-Dats.home="${BASEDIR}" -Dats.type="${SYSTEM}" ${MAIN} ${CONFIG} >> ${LOGS}/screen.log &

echo "starting ${SYSTEM}"
echo "config: ${BASEDIR}/${CONFIG}"
echo "log: ${LOGS}/app.log"
}


function startup_microservice {
BASEDIR=$(cd `dirname $0`; pwd)
MAIN=$1
CONFIG=$2
PROFILE=$3
SYSTEM=$4

create_log_directory
get_delimiter
import_extension

HEAP_SIZE=$(heapsizemb 0.7)

java -server -d64 -Xms${HEAP_SIZE}m -Xmx${HEAP_SIZE}m \
${GC_LOG_CONTENT_ARGS} \
${GC_ARGS} \
-cp "${BASEDIR}/bin/*${DELIMITER}${BASEDIR}/lib/*${DELIMITER}${BASEDIR}/conf/*${DELIMITER}${BASEDIR}/conf/common/*${DELIMITER}${BASEDIR}/strategy/*${DELIMITER}" \
-Dlocation="${BASEDIR}" -Dlogging.config="classpath:conf/profile/log4j2.xml" \
-Dspring.config.location=classpath:${CONFIG} -Dspring.profiles.active=${PROFILE} \
-DapolloEnv="prod" -DPREFIX_IP=$PREFIX_IP \
-Dmorphling.sysno="001298@XTrader-Algo" \
-Dats.home="${BASEDIR}" -Dats.type="${SYSTEM}" ${MAIN} >> ${LOGS}/screen.log &

echo "starting ${SYSTEM}"
echo "config: ${BASEDIR}/${CONFIG}"
echo "log: ${LOGS}/app.log"
}


function startup_matic {
BASEDIR=$(cd `dirname $0`; pwd)
MAIN=$1
CONFIG=$2
SYSTEM=$3

create_log_directory
get_delimiter
import_extension

HEAP_SIZE=$(heapsizegb 0.6)

java -server  -d64 -Xms${HEAP_SIZE}G -Xmx${HEAP_SIZE}G \
-XX:+UseG1GC \
-XX:+ParallelRefProcEnabled \
-Xloggc:log/gc.log.$(date +%Y-%m-%d-%H-%M) \
-XX:MaxGCPauseMillis=400 \
-XX:+PrintGCDateStamps \
-XX:+PrintHeapAtGC \
-XX:+HeapDumpOnOutOfMemoryError \
-XX:HeapDumpPath=log/gcdump \
-Dcom.sun.management.jmxremote.port=9999 \
-Dcom.sun.management.jmxremote.ssl=false \
-Dcom.sun.management.jmxremote.authenticate=false \
-cp "${BASEDIR}/bin/*${DELIMITER}${BASEDIR}/lib/*${DELIMITER}${BASEDIR}/conf/*${DELIMITER}${BASEDIR}/conf/common/*${DELIMITER}${BASEDIR}/strategy/*${DELIMITER}" \
-Dlocation="${BASEDIR}" -Dlog4j.configurationFile="conf/profile/log4j2.xml" \
-Dats.home="${BASEDIR}" -Dats.type="${SYSTEM}" ${MAIN} ${CONFIG} >> ${LOGS}/screen.log &

echo "starting ${SYSTEM}"
echo "config: ${BASEDIR}/${CONFIG}"
echo "log: ${LOGS}/app.log"
}


function kill_processor {
BASEDIR=$(cd `dirname $0`; pwd)
SYSTEM=$1

    G_PROCESS=`ps -ef | grep ${BASEDIR} | grep ${SYSTEM} | grep -v grep | grep -v stop | grep -v restart | awk '{print $2}'`
    for i in ${G_PROCESS}
    do
        echo "kill ${SYSTEM} process id: $i, location: ${BASEDIR}"
        kill $i
    done
}

function processor_is_killed {
    kill -0 $1 > /dev/null 2>&1
    echo $?
}

function create_log_directory {
BASEDIR=$(cd `dirname $0`; pwd)
LOGS=${BASEDIR}/log/${SYSTEM}

if [ ! -d ${LOGS} ]
then
    mkdir -p ${LOGS}
fi
}

function get_delimiter {
OS=`uname`

if  [[ ${OS} =~ "Linux" ]]
then
    DELIMITER=':'
else
    DELIMITER=';'
fi
}


function import_extension {
get_delimiter
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${BASEDIR}/ext/linux_x64/${DELIMITER}${BASEDIR}/ext/windows_x64/
}

function timeout_force_kill() {
    local PID=${1}
    local LOOP_NUM=${2}
    for((integer = 1; integer <= ${LOOP_NUM}; integer++))
    do
        sleep 1s
        isKilled=$(processor_is_killed "${PID}")

        if [[ ${isKilled} != "0" ]] ; then
            return;
        elif [[ ${integer} -eq ${LOOP_NUM} ]]  ; then
            echo "kill gracefully fail, kill algo by force"
            kill -9 "${PID}"
            timeout_force_kill ${PID} ${LOOP_NUM}
            return;
        fi
    done
}
