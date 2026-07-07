#!/bin/bash
if [ -n "$1" ]
then
        if [ $1 = "-k" ] 
        then
                ps -ef | grep jobserver.py | grep -v 'grep' | awk '{print $2}' | xargs kill -9
                ps -ef | grep jobworker.py | grep -v 'grep' | awk '{print $2}' | xargs kill -9
        else
                echo 'command -k'
        fi

else
        echo $1
        python mining_package03/jobqueue/jobserver.py &
        sleep 0.5s
        #create many workers
        python mining_package03/jobqueue/jobworker.py &
        python mining_package03/jobqueue/jobworker.py &
        python mining_package03/jobqueue/jobworker.py &
        python mining_package03/jobqueue/jobworker.py &
        python mining_package03/jobqueue/jobworker.py &
        python mining_package03/jobqueue/jobworker.py &
fi

