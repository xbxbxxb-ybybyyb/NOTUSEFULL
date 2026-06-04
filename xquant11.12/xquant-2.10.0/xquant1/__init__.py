import os
os.environ['ENV_VERSION'] = 'prd'
os.environ['XQUANT_CONF_FILE'] = '/etc/.config/xquant_conf'

import sys
try:
    import xquant1.xqutils
    sys.modules["xquant1.utils"] = sys.modules["xquant.xqutils"]
except:
    pass

try:
    import xquant1.xqutils.xqfile
    sys.modules["xquant1.pyfile"] = sys.modules["xquant.xqutils.xqfile"]
except:
    pass

try:
    import xquant1.xqutils.xqlog
    sys.modules["xquant1.log"] = sys.modules["xquant.xqutils.xqlog"]
except:
    pass

try:
    import xquant1.strategy.backtest
    sys.modules["xquant1.backtest"] = sys.modules["xquant.strategy.backtest"]
except:
    pass

try:
    import xquant1.thirdpartydata.factor
    sys.modules["xquant1.factor"] = sys.modules["xquant.thirdpartydata.factor"]
    sys.modules["xquant1.factor.FactorEnum"] = sys.modules["xquant.thirdpartydata.factor.FactorEnum"]
except:
    pass

try:
    import xquant1.xqutils.xqfile.ftpfile
    sys.modules["xquant.pyfile.ftp"] = sys.modules["xquant.xqutils.xqfile.ftpfile"]
except:
    pass

try:
    import xquant1.xqutils.pyfilelib
    sys.modules["xquant.pyfilelib"] = sys.modules["xquant.xqutils.pyfilelib"]
except:
    pass

try:
    import xquant1.thirdpartydata.multifactor
    sys.modules["xquant.multifactor"] = sys.modules["xquant.thirdpartydata.multifactor"]
except:
    pass

try:
    import xquant1.compute.aimr
    sys.modules["xquant.tensorflow"] = sys.modules["xquant.compute.aimr"]
except:
    pass
