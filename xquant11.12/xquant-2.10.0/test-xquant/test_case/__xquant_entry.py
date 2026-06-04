
import sys
import os
os.environ['USER_TEAM_ID']=str(120)
__share_folders=[{"name":"华泰证券","type":"company","id":1},{"name":"证券投资部","type":"department","id":2},{"name":"系统团队","type":"team","id":120}]

from xquant.pyfile import set_xquant_entry
set_xquant_entry(__share_folders)
from xquant.sandbox.sandbox import init_sandbox
init_sandbox()
main = None
if os.environ.get('IS_DOCKER',False):
    import os
    fp,fn = os.path.split(sys.argv[4])
    if fp!="":
        sys.path.append("./"+fp)
        sys.path.append(os.path.abspath(fp))
    __import__(fn)
else:
    from tt import *
if main:
    main()
