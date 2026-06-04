from xquant.pyfile import Pyfile

start_date = 20190701
end_date = 20190831
cv_suffix = 1

py = Pyfile()

src_path1 = "Apollo/cv_results/buy{}/{}-{}_universal/".format(cv_suffix, start_date, end_date)
src_path2 = "Apollo/cv_results/sell{}/{}-{}_universal/".format(cv_suffix, start_date, end_date)

dst_path1 = "Apollo/cv_results/{}-{}_universal/buy/".format(start_date, end_date)
dst_path2 = "Apollo/cv_results/{}-{}_universal/sell/".format(start_date, end_date)

if not py.exists(dst_path1):
    py.mkdir(dst_path1)

for file in py.listdir(src_path1):
    py.copyToShare(dst_path1, src_path1 + file)

if not py.exists(dst_path2):
    py.mkdir(dst_path2)

for file in py.listdir(src_path2):
    py.copyToShare(dst_path2, src_path2 + file)
