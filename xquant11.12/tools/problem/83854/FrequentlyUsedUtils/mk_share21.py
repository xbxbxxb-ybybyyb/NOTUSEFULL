# from xquant.pyfile import Pyfile
# py = Pyfile()


# py.mkdir('$21/test_makedir/') 


from xquant.pyfilelib import Pyfile
py = Pyfile()

print(py.getShareFolders("team"))
py.mkdir('$21/test_makedir_1/')