import ray
from SignalConfig import SignalConfig
from Common.CalculationScheduler import CalculationScheduler
from shutil import copyfile
import os

def main():
    copyfile("/data/user/013050/chensf/Job.py", "/opt/anaconda3/lib/python3.6/site-packages/QuantFramework/System/Job.py")
    os.system("cat /opt/anaconda3/lib/python3.6/site-packages/QuantFramework/System/Job.py")
    signalConfig = SignalConfig(enable=True)
    if len(signalConfig.task_list) > 0:
        calculationScheduler = CalculationScheduler()
        calculationScheduler.setSignalConfig(signalConfig)
        calculationScheduler.startCalculation()


if __name__ == "__main__":
    main()




