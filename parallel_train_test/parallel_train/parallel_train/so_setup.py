# -* -coding: UTF-8 -* -
__author__ = 'Arvin'

"""
执行前提：
    系统安装python-devel 和 gcc
    Python安装cython

编译整个当前目录：
    python py-setup.py
编译某个文件夹：
    python py-setup.py BigoModel

生成结果：
    目录 build 下

生成完成后：
    启动文件还需要py/pyc担当，须将启动的py/pyc拷贝到编译目录并删除so文件

python eval语法不支持
retry不支持，支持retrying
装饰器单例不支持
"""

import sys, os, shutil, time
import distutils.core
from Cython.Build import cythonize

starttime = time.time()
currdir = os.path.abspath('.')
parentpath = sys.argv[1] if len(sys.argv) > 1 else ""
setupfile = os.path.join(os.path.abspath('.'), __file__)
build_dir = "build"
build_tmp_dir = build_dir + "/temp"
# 文件名过滤列表,不删除
name_ignore_files = ['__init__.py', ]
# 路径过滤列表,不转换为so,helper内部类错误,其他内部方法跟lambda方法无法pickle
path_ignore_files = ['helper.py', 'train/backend.py', 'train/checkpoint.py',
                     'train/trainer.py', 'train/session.py']

# 全部转换为so包后会出现的问题,目前部分放开：
# cython 打包由于使用到 dataclasses ，cython 版本必须大于等于3.0.0
# cython 打包对于 ray ，无法使用内部类（解决方案放开helper.py）
# cython 打包后无法 pickle 局部方法（解决方案，更改train源码所有局部方法和 lambda 方法更改作用域为全局）
# cython 打包后对于Tensorflow报错TypeError: can't pickle _LazyLoader objects,
# (官方解决方案: http://44.228.130.106/using-ray-with-tensorflow.html, 将tensorflow的import放至并行方法中)


def getpy(basepath=os.path.abspath('.'), parentpath='', name='', excepts=(), copyOther=False, delC=False):
    """
    获取py文件的路径
    :param basepath: 根路径
    :param parentpath: 父路径
    :param name: 文件/夹
    :param excepts: 排除文件
    :param copy: 是否copy其他文件
    :return: py文件的迭代器
    """
    fullpath = os.path.join(basepath, parentpath, name)
    for fname in os.listdir(fullpath):
        ffile = os.path.join(fullpath, fname)
        # print basepath, parentpath, name,file
        if os.path.isdir(ffile) and fname != build_dir and not fname.startswith('.'):
            for f in getpy(basepath, os.path.join(parentpath, name), fname, excepts, copyOther, delC):
                yield f
        elif os.path.isfile(ffile):
            ext = os.path.splitext(fname)[1]
            if ext == ".c":
                if delC and os.stat(ffile).st_mtime > starttime:
                    os.remove(ffile)
            elif ffile not in excepts and os.path.splitext(fname)[1] not in ('.pyc', '.pyx'):
                if os.path.splitext(fname)[1] in ('.py', '.pyx') \
                        and not fname.startswith('__') \
                        and fname not in name_ignore_files \
                        and os.path.join(parentpath, name, fname) not in path_ignore_files:
                    yield os.path.join(parentpath, name, fname)
                elif copyOther:
                    dstdir = os.path.join(basepath, build_dir, parentpath, name)
                    if not os.path.isdir(dstdir): os.makedirs(dstdir)
                    shutil.copyfile(ffile, os.path.join(dstdir, fname))
        else:
            pass


# 获取py列表
module_list = list(getpy(basepath=currdir, parentpath="", excepts=(setupfile)))
try:
    distutils.core.setup(ext_modules=cythonize(module_list, compiler_directives={'language_level': '3'}),
                         script_args=["build_ext", "-b", build_dir, "-t", build_tmp_dir])
except Exception as e:
    raise e
else:
    module_list = list(getpy(basepath=currdir, parentpath="", excepts=(setupfile), copyOther=True))
module_list = list(getpy(basepath=currdir, parentpath="", excepts=(setupfile), delC=True))

if os.path.exists(build_tmp_dir):
    shutil.rmtree(build_tmp_dir)

# 拷贝so文件至当前目录
os.system("cp -R build/parallel_train/* ../parallel_train/")

# 删除非__init__的py文件，删除build文件夹
for root, dirs, files in os.walk('./'):
    for name in files:
        if name not in name_ignore_files \
                and not name.endswith('.so') \
                and os.path.join(root, name).replace('./', '') not in path_ignore_files:
            os.remove(os.path.join(root, name))
    for name in dirs:
        if name == 'build':
            shutil.rmtree(os.path.join(root, name))

print("complate! time:", time.time() - starttime, 's')
