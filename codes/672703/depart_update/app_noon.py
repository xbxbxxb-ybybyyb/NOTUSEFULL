import datetime 
import sys
sys.path.insert(0,'depart_update/')
from update_depart_sample import *
today = datetime.date.today().strftime('%Y%m%d')
update_sample(today, mode=2) 