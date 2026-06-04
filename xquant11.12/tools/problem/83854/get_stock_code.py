import os

stock_code = os.listdir("/app/data/013050/chensf/AppleData/")
stock_code.sort()
for code in stock_code:
    print ("[\"" + code + "\"],")