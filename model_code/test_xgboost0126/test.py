import os
import time
start = time.time()
os.system("pip install --no-cache-dir --no-deps /data/user/013150/tick_data/dol_pre_install_pkgs/pandas-0.25.1-cp36-cp36m-manylinux1_x86_64.whl >> out.log")
os.system("pip install --no-cache-dir --no-deps /data/user/013150/tick_data/dol_pre_install_pkgs/dolphindb-1.30.0.12-cp36-cp36m-manylinux2010_x86_64.whl >> out.log")
end = time.time()
print(end-start)
