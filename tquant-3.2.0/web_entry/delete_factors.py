import os
import time

from SmartFactor.FactorCalc import run_factors_days, run_securities_days
from tquant.psfactor import PsFactorData

factors = os.environ.get('factors')
psfactor = PsFactorData()
library_name = psfactor.get_library_name_by_factor(factors, 'release')
psfactor.delete_factors(library_name, factors)
