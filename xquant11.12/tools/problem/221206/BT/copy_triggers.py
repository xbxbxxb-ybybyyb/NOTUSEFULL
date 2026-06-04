from xquant.pyfile import Pyfile


def main(today):
    src_path = "/data/user/666888/Apollo/parameters/Apollo_{}/".format(today)
    dst_path = "Apollo/bt_triggers/{}/".format(today)

    py = Pyfile()
    if not py.exists(dst_path):
        py.mkdir(dst_path)

    py.upload(dst_path, src_path)


if __name__ == "__main__":
    today = "20191209"
    main(today)