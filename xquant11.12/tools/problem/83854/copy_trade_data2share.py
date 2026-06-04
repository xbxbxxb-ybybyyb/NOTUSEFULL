from xquant.pyfile import Pyfile


py = Pyfile()
if py.exists('TEMP'):
    py.delete('TEMP', recursive=True)
py.upload('TEMP/20181024-20181224/5161101+alpha/', '/app/data/666888/BT_Trade_OrderCapacity/20181024-20181224/5161101+alpha/')
py.copyToShare('$21/ModelProduction/20180901_end/bt_info/20181024-20181224/5161101+alpha/', 'TEMP/20181024-20181224/5161101+alpha/')
py.delete('TEMP', recursive=True)
