# _*_ coding:utf-8 _*_

try:
    import ray
    from .basic_data import *
    from .stock_data import *
    from .index_data import *
    from .fund_data import *
    from .psfactor import *
except Exception as e:
    print(repr(e))
finally:
    print('''        ,----,                                                                 
      ,/   .`|                                                                 
    ,`   .'  :  ,----..                                                ___     
  ;    ;     / /   /   \                                             ,--.'|_   
.'___,/    ,' /   .     :            ,--,                    ,---,   |  | :,'  
L    :     | .   /   ;.  \         ,'_ /|                ,-+-. /  |  :  : ' :  
;    R.';  ;.   ;   /  ` ;    .--. |  | :    ,--.--.    ,--.'|'   |.;__,'  /   
`----'  |  |;   |  ; \ ; |  ,'_ /| :  . |   /       \  |   |  ,"' ||  |   |    
    '   :  ;|   :  | ; | '  |  ' | |  . .  .--.  .-. | |   | /  | |:__,'N :    
    |   |  '.   |  ' ' ' :  |  | ' |  | |   \__\/: . . |   H |  | |  '  : |__  
    '   :  |'   ;  \; L  |  :  | : ;  ; |   ," .--.; | |   | |  F/   |  S '.'| 
    ;   |.'  \   S  ',  . \ '  :  `--'   \ /  /  ,.  | |   | Y--'    ;  :    ; 
    '---'     ;   :      ; |:  ,      .-./;  :   .'   \|   |/        |  ,   W  
               \   J .'`--"  `--`----'    |  ,     .-./'---'          ---`-'   
                `---`                      `--`---'                            
                                                                               ''')

import sys
import logging

try:
    from .logger import setup_logging
    tq_logger = setup_logging("quant_info")
except:
    #unkown error fund
    tq_logger = logging.getLogger('mylogger')
    tq_logger.setLevel(logging.WARNING)
