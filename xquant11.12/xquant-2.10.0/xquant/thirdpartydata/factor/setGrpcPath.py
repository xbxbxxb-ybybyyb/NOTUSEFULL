from xquant.setXquantEnv import xquantEnv,testEnv
if xquantEnv == 0:
    if testEnv == 40:
        md_channels = ['168.61.13.42:30014']
    elif testEnv == 63:
        md_channels = ['168.63.129.52:30014']
elif xquantEnv == 1:
    md_hash = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    md_channels = ['168.9.38.53:30014']
    # 这里ratio为占比，注意这里占比总数为100，请设置时勿计算错误
    md_set_channels = \
        [
            {'ip': '168.9.38.53', 'port': 30014, 'ratio': 100}
        ]
if __name__ == '__main__':
    """
    写入头部的md_hash数列，由于是直接读取并写入本文件修改main内代码请检查清楚
    """
    import random
    ins = []
    for i in range(100):
        while True:
            tmp = int(random.random() * len(md_set_channels))
            if md_set_channels[tmp].get('ratio') > 0:
                md_set_channels[tmp]['ratio'] = md_set_channels[tmp].get('ratio') - 1
                ins.append(tmp)
                break
    lines =[]
    with open(__file__,'rb') as f:
        for line in f.readlines():
            lines.append(line)
    if str(lines[0]).find("md_hash")==-1:
        lines.insert(0,bytes("md_hash="+str(ins)+"\r\n",'utf-8'))
    else:
        lines[0]= bytes("md_hash="+str(ins)+"\r\n",'utf-8')
    with open(__file__,"wb") as f:
        f.writelines(lines)
    