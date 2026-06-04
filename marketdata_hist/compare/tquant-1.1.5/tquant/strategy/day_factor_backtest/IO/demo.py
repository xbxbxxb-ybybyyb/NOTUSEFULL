import os
import pandas as pd
import numpy as np
from day_factor_backtest.IO import IO
from day_factor_backtest.IO.IO_enums import *

start_date = '20190101'
end_date = '20190601'
columns = 'close'
res = IO.read_data([start_date, end_date], [columns], ftype=FType.MD, dsource=DSource.WIND)[columns].unstack()
res.tail()
