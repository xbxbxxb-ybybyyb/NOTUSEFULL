import os
import time
from xquant.xqutils.helper import link
lm = link.LinkMessage()
path = os.getcwd()

print('Start')
today = int(time.strftime('%Y%m%d'))
# today = 20200612
lm.sendMessage("HQF_Update on {} starts ".format(today))

t1 = time.time()
os.system("python3 {}/HQF/Main.py".format(path))
os.system("python3 {}/HQF/Updater/Parallel4GetHBase.py".format(path))
os.system("python3 {}/HQF/Updater/CheckDailyData.py".format(path))

if os.path.exists('/data/user/015618/HQF_Update_Log/{}/{}_HFF.part1'.format(today,today)):
    pass
else:
    lm.sendMessage("HQF_Update on {} failed ".format(today))
    exit()
os.system("python3 {}/HQF/Updater/Concat.py".format(path))
print('Total HQF task costs {} seconds'.format(time.time()-t1))
lm.sendMessage("HQF_Update on {} ends ".format(today))