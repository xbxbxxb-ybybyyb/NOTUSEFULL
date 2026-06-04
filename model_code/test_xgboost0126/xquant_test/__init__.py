import sys
import logging
    
try:
    from xquant.xqutils.xqlog.logger import setup_logging
    setup_logging()
    xq_logger = logging.getLogger("quant_info")
except:
    #unkown error fund
    xq_logger = logging.getLogger('mylogger')
    xq_logger.setLevel(logging.WARNING)


try:
    import xquant.xqutils
    sys.modules["xquant.utils"] = sys.modules["xquant.xqutils"]
except:
    pass

try:
    import xquant.xqutils.xqfile
    sys.modules["xquant.pyfile"] = sys.modules["xquant.xqutils.xqfile"]
except:
    pass

try:
    import xquant.xqutils.xqlog
    sys.modules["xquant.log"] = sys.modules["xquant.xqutils.xqlog"]
except:
    pass

try:
    import xquant.xqutils.xqfile.ftpfile
    sys.modules["xquant.pyfile.ftp"] = sys.modules["xquant.xqutils.xqfile.ftpfile"]
except:
    pass

try:
    import xquant.xqutils.pyfilelib
    sys.modules["xquant.pyfilelib"] = sys.modules["xquant.xqutils.pyfilelib"]
except:
    pass

