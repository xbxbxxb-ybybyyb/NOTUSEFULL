import os
import shutil
is_day_factor = False
weekdays = False
if is_day_factor:
    path = '/data/user/015618/Apollo'
else:
    path = '/data/user/015618/Apollo/MyFactors/Test'
if weekdays:
    source = os.path.join(path,'factor_report')
    desti = os.path.join(path,'factor_report_thisweek')
else:
    source = os.path.join(path,'factor_report_thisweek')
    desti = os.path.join(path,'factor_report_his')

files = os.listdir(source)
for f,file in enumerate(files):
    shutil.move(os.path.join(source,file),os.path.join(desti,file))
    print(str(f+1)+'/'+str(files.__len__()))