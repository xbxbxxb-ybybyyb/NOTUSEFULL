from enum import Enum, unique

@unique
class DType(Enum):
    STOCK   = 1
    FUTURES = 2
    SPOT    = 3
    INDEX   = 4

@unique
class DFreq(Enum):
    TICK      = 1
    MINUTE    = 2
    DAILY     = 3
    WEEKLY    = 4
    QUARTERLY = 5
    MONTHLY   = 6
    YEARLY    = 7

@unique
class DSource(Enum):
    HTSC = 1
    WIND = 2
    OPTM = 3
    STYLEFACTOR = 4
    STYLE=5
    WEIGHT=6
    

@unique
class UniType(Enum):
    HS300 = 1
    ZZ500 = 2
    SZ50  = 3

@unique
class MktType(Enum):
    CHINA = 1
    HK    = 2
    US    = 3

@unique
class FType(Enum):
    FDD      = 1 # Fundamental Data
    MD       = 2 # Market Data
    FCD      = 3 # Forcast Data
    FACTOR   = 4 # Factor Data
    ALPHA    = 5 # Alpha Factor
    RISK     = 6 # Risk Factor
    UNIV     = 7 # Universe Data
    INDUSTRY = 8 # Industry Data
    CALENDAR = 9 # Calendar Data
    FWD5     = 10
    FWD10    = 11
