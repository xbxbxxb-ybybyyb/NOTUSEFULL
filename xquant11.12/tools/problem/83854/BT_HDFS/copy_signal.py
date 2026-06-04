from xquant.pyfile import Pyfile
import os, shutil
import uuid

def copy_signal2share(upload_date, symbols, src_path, dest_path):
  # upload_date = ['20181211']  # empty means all; or e.g. ['20180901']
    py = Pyfile()

    for symbol in symbols:
        for date in upload_date:
            source_file_dir = src_path+symbol+"/"+date
            dest_file_dir = dest_path+symbol+"/"
            print(source_file_dir, dest_file_dir)
            py.copyToShare(dest_file_dir, source_file_dir + '/')
    
    
    # try:
        # py.copyToShare(dest_path, temp_path + '/')
        # py.delete(temp_path, recursive=True)
    # except:
      # print("error copy signal")
    
    
    
def main():
    upload_date = ["20190301"] # empty means all; or e.g. ['20180901']
    symbols =  ['603602.SH']
    # src_path = '/app/data/666888/ModelProduction/2018-10-01/20190225/ModelSignalDataSet/'
    src_path = 'output/2018-10-01/ModelSignalDataSet/'
    dest_path = '$21/ModelProduction/20181001_end/signals/'
    # dest_path = '$21/ModelProduction/20181001_end/2018-10-01/'
    print(upload_date)
    print(src_path)
    copy_signal2share(upload_date, symbols, src_path, dest_path)


if __name__ == "__main__":
    main()    