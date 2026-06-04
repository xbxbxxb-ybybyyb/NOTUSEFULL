from enum import Enum, unique
from enum import IntEnum

@unique
class PRICE(IntEnum):
    """
    - ADJ_ORIGINAL 未复权
    - ADJ_FORWARD 前复权
    - ADJ_BACKWARD 后复权
    """
    ADJ_ORIGINAL = 0
    ADJ_FORWARD = 1
    ADJ_BACKWARD = 2
    

class FS(IntEnum):
    """
    - AS_BEFORE_2017 旧会计准则（2017版本之前）
    - AS_2017  新会计准则 （2017版本）
    
    - CFT_CONSOLIDATED 合并报表
    - CFT_ORIGINAL 母公司
    
    - ADJ_ORIGINAL 原始报表
    
    - DAY_NATURAL  自然日
    - DAY_TRADING  A股交易日
    """
    AS_BEFORE_2017 = 4
    AS_2017 = 0
    
    # 合并报表
    CFT_CONSOLIDATED = 16
    # 母公司
    CFT_ORIGINAL = 0
    
    # 原始报表
    ADJ_ORIGINAL = 0

class DAY(IntEnum):
    NATURAL = 0 # 自然日
    TRADING = 128 # A股交易日

@unique
class FILT_TYPE(IntEnum):
    """
    - SUSPENSION 停牌
    - HARDEN 涨停
    - FALLING 跌停
    - OPENING_HARDEN  开盘涨停
    - OPENING_FALLING  开盘跌停
    ===================  ======================================================
        枚举类型                     说   明
    -------------------  ------------------------------------------------------
      SUSPENSION          停牌( 交易状态为零 )
      HARDEN              涨停( (当时最高价-前收盘价) / 前收盘价 > 0.099 )
      FALLING             跌停( (当时最低价-前收盘价) / 前收盘价 < -0.099 )
      OPENING_HARDEN      开盘涨停( (开盘价-前收盘价) / 前收盘价 > 0.099 )
      OPENING_FALLING     开盘跌停( (开盘价-前收盘价) / 前收盘价 < -0.099 )
    -------------------  ------------------------------------------------------
                            组  合  示  例
    ---------------------------------------------------------------------------
      SUSPENSION + HARDEN               停牌+涨停
      SUSPENSION + FALLING              停牌+跌停
      OPENING_HARDEN + SUSPENSION       开盘涨停+停牌
      OPENING_FALLING + SUSPENSION      开盘跌停+停牌
    =================================  ========================================
    """
    SUSPENSION = 1  #停牌
    HARDEN = 2 #涨停
    FALLING = 4 #跌停
    OPENING_HARDEN = 8 # 开盘涨停
    OPENING_FALLING = 16 # 开盘跌停
    
@unique
class FREQUENCY_ENUM(IntEnum):
    DAY = 1
    WEEK =2
    MONTH =3
    QUARTER =4
    HALFYEAR = 5
    YEAR = 6

@unique
class TANSDAY_DATE_TYPE(IntEnum):
    """
    - ALLDAYS  日历日
    - TRADINGDAYS  交易日
    """
    ALLDAYS = 1 # 日历日
    TRADINGDAYS = 2  # 交易日
    
@unique
class PLATETYPE(IntEnum):
    CONCEPT = 1 #概念板块;
    INDEX = 2 #指数板块;
    MARKET = 3 #市场板块;
    industry = 4 #行业板块