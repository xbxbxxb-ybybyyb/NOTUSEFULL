import os
target_securities_sh = [
    '688599.SH','688012.SH','688303.SH',
    '688521.SH','688385.SH','688036.SH',
    '689009.SH','688598.SH','688536.SH',
    '688111.SH','688017.SH','688981.SH',
    '688116.SH','688223.SH','688777.SH',
    '688008.SH','688256.SH','688271.SH',
    '688009.SH','688561.SH','688126.SH',
    '688297.SH','688220.SH','688187.SH',
    '688772.SH','688390.SH','688567.SH',
    '688005.SH','688122.SH','688006.SH',
    '688819.SH','688728.SH','688126.SH',
    '688208.SH','688778.SH','688070.SH',
    '688234.SH','688375.SH','688350.SH',
    '688598.SH','688198.SH','688396.SH',
    '688099.SH','688161.SH','688065.SH',
    '688169.SH','688082.SH','688180.SH',
    '688499.SH','688041.SH','688105.SH',
    '688047.SH','688052.SH','688114.SH',
    '688538.SH','688348.SH','688295.SH',
    '688779.SH','688178.SH','688349.SH',
    '688219.SH',
    '688029（l2p）.SH',
    '688012(l2p).SH',
]

target_securities_sh300 = ["603019.SH", "600188.SH", "300763.SZ", "300122.SZ",
                     "000858.SZ", "002594.SZ", "300760.SZ", "605117.SH", "600732.SH", "002230.SZ", "300059.SZ"]


target_securities_sh.extend(target_securities_sh300)
print(target_securities_sh)

factor_group_num = 8
for symbol in target_securities_sh:
    os.system("echo > {}.log".format(symbol))
    for factor_group in range(factor_group_num):
        os.system("ps -ef|grep dol|grep -v grep|awk '{print $2}'|xargs kill -9")
        os.system("cd ~/server/ && sh startSingle.sh")
        os.system("python3 main_select.py {} {} >> {}.log".format(symbol, factor_group, symbol))
