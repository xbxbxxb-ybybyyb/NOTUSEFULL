from xquant.pyfile import Pyfile
import os, shutil
import uuid

def copy_signal2share(upload_date, symbols, src_path, dest_path):
    

    # upload_date = ['20181211']  # empty means all; or e.g. ['20180901']
    # symbols = []
    # path = '/app/data/013050/chensf/tmp/ModelSignalDataSet/'
    
    temp_path = 'TEMP' + str(uuid.uuid1())
    if len(symbols) == 0:
        symbols = os.listdir(src_path)
        symbols.sort()
    py = Pyfile()
    if len(upload_date) == 0:
        # start = 500
        # end = len(symbols)
        # print('{} to {} in {}...'.format(str(start), str(end), str(len(symbols))))
        # for i in range(start, end):
        for symbol in symbols:
            # symbol = symbols[i]
            dates = os.listdir(src_path + symbol)
            for date in dates:
                py.upload(temp_path + '/' + symbol, src_path + symbol + '/' + date)
    else:
        for symbol in symbols:
            for date in upload_date:
                filename = symbol + '_' + date + '.csv'
                if os.path.exists(src_path + symbol + '/' + date + '/' + filename):
                    py.upload(temp_path + '/' + symbol, src_path + symbol + '/' + date)
                # else:
                    # print(symbol)

    print('copying to the shared team folder.')
    # py.copyToShare('$21/ModelProduction/20180901_end/signals/', 'TEMP/')
    print(dest_path, temp_path)
    try:
        py.copyToShare(dest_path, temp_path + '/')
        py.delete(temp_path, recursive=True)
    except:
        print("error copy signal")
    
    
def main():
    upload_date = []  # empty means all; or e.g. ['20180901']
    # symbols = []
    symbols = os.listdir('/app/data/666888/ModelProduction/2019-03-01/20190506/ModelSignalDataSet/')
    symbols.sort()
    symbols = symbols[:200]
    
    # src_path = '/app/data/666888/ModelProduction/2019-01-01/20190412/ModelSignalDataSet/'
    src_path = '/app/data/666888/ModelProduction/2019-03-01/20190506/ModelSignalDataSet/'
    # dest_path = '$21/ModelProduction/20190101_end/signals/'
    dest_path = '$21/ModelProduction/20190101_48_end/signals/'
    print(upload_date)
    print(src_path)
    copy_signal2share(upload_date, symbols, src_path, dest_path)


if __name__ == "__main__":
    main()
    
