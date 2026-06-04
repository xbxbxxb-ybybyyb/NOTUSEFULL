cp automining-1.7.4.tar.gz /home/appadmin/automining-1.7.4.tar.gz 
cp DolphinDB_Linux64_V2.00.12.2.zip /home/appadmin

cd /home/appadmin
# update automining python sdk
#curl ftp://168.8.2.68/016869/dolphin_server/automining-1.7.4.tar.gz -u "ftphzh:ftphzh2602" -O
pip install /home/appadmin/automining-1.7.4.tar.gz --no-deps
# update Dolphindb server
#curl ftp://168.8.2.68/016869/dolphin_server/DolphinDB_Linux64_V2.00.12.2.zip -u "ftphzh:ftphzh2602" -O
unzip -o DolphinDB_Linux64_V2.00.12.2.zip
# start dolphindb server
cd server && chmod -R 777 dolphindb && curl ftp://168.8.2.68/016869/dolphindb.lic -u "ftphzh:ftphzh2602" -O && sh startSingle.sh $1 $2


ln -s /data/user/016869/AutoMiningFrame/resource/ats-quant-factor-engine/L3FactorFrame/ /opt/anaconda3/lib/python3.11/site-packages/

#pip install --upgrade -i http://repo.htzq.htsc.com.cn/repository/htscpypi/simple/ --trusted-host repo.htzq.htsc.com.cn 
