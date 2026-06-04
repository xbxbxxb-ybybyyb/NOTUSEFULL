# _*_ coding:utf-8 _*_
import sys
import os
import yaml
import shutil
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
from .cmo import tracking as cmo_tracking
from .reserved_metrics import reserved_metrics


USE_CMO = {}


def get_use_cmo():
    global USE_CMO
    if not USE_CMO:
        if os.environ.get('use_cmo'):
            USE_CMO['use_cmo'] = True
        else:
            with open("/etc/.config/xquant_conf", 'r') as f:
                conf = f.readlines()
                entryfilePath = [i for i in conf if i.startswith('entryFilePath=')][0]
                file_path = entryfilePath.split('=')[1].replace('\n', '')
                if file_path:
                    USE_CMO['use_cmo'] = True
                else:
                    USE_CMO['use_cmo'] = False
    return USE_CMO['use_cmo']


def __check_params(params_name, params):
    if not params:
        raise Exception('必须传入{}'.format(params_name))
    for key, value in params.items():
        if not isinstance(key, str):
            raise Exception(
                '{}中的键必须为str, {}为{}'.format(
                    params_name, key, str(type(key))))


def parse_params(config_path=None):
    def search_yaml(current_path):
        if current_path == '':
            raise Exception('未找到yaml')
        file_list = os.listdir(current_path)
        yamls = []
        for file_name in file_list:
            if file_name == 'model_config.yaml':
                yamls.append(file_name)
        if len(yamls) == 1:
            return os.path.join(current_path, yamls[0])
        elif len(yamls) == 0:
            current_path_list = current_path.split('/')
            if len(current_path_list) != 1:
                return search_yaml('/'.join(current_path_list[:-1]))
            else:
                raise Exception('未找到yaml')
        else:
            raise Exception('yaml数量不止一个:{}'.format(str(yamls)))

    def is_head_node():
        import socket
        import ray
        local_ip = socket.gethostbyname(socket.gethostname())
        for cluster in ray.nodes():
            if cluster['NodeManagerAddress'] == local_ip:
                return True
        return False

    def get_head_node_ip_port():
        import socket
        import ray
        local_ip = socket.gethostbyname(socket.gethostname())
        for cluster in ray.nodes():
            if local_ip in str(cluster['Resources']):
                return cluster['NodeManagerAddress'], cluster['NodeManagerPort']
        return None


    if config_path:
        if not os.path.exists(config_path):
            raise Exception('路径{}不存在'.format(config_path))
        if '.' in config_path.split('/')[-1]:
            if config_path.split('/')[-1] != 'model_config.yaml':
                raise Exception('传入的文件名不是model_config.yaml')
        else:
            file_list = os.listdir(config_path)
            found_yaml = False
            for file_name in file_list:
                if file_name == 'model_config.yaml':
                    config_path = os.path.join(config_path, file_name)
                    found_yaml = True
                    break
            if not found_yaml:
                raise Exception('传入的路径中未发现model_config.yaml')
        yaml_file = config_path
        with open(yaml_file, 'r') as f:
            params_dict = yaml.safe_load(f.read())
    else:
        import ray
        # ray not initialized, read yaml file
        if not ray.is_initialized():
            print("not inited")
            # header node return yaml_config
            current_path = '/'.join(os.path.realpath(sys.argv[0]).split('/')[:-1])
            yaml_file = search_yaml(current_path)
            with open(yaml_file, 'r') as f:
                params_dict = yaml.safe_load(f.read())
            try:
                dst = '/opt/anaconda3/lib/python3.6/site-packages/ray/workers'
                if os.path.exists(dst):
                    shutil.copyfile(yaml_file, os.path.join(dst, yaml_file.split('/')[-1]))
            except:
                pass
            return params_dict

        # ray has initialized, head node save params to redis, child node read params
        import redis
        import json
        try:
            ip, port = get_head_node_ip_port()
            client = redis.StrictRedis(host=ip, port=6379, password='5241590000000000')
        except:
            raise Exception("连接redis主节点失败")
        if not is_head_node():
            # 子节点获取配置
            params_dict = json.loads(client.get(ip+'_'+port))
        else:
            # header node save yaml_config
            current_path = '/'.join(os.path.realpath(sys.argv[0]).split('/')[:-1])
            yaml_file = search_yaml(current_path)
            with open(yaml_file, 'r') as f:
                params_dict = yaml.safe_load(f.read())
            # 主节点未保存当前ip端口，则保存model_yaml
            ip_port = ip+'_'+str(port)
            if not client.exists(ip_port):
                client.set(ip_port, str(params_dict), ex=10)

    return params_dict


def __get_model_name(params=None):
    if not params:
        params = parse_params()
    try:
        model_name = params['model']['name']
    except Exception as e:
        raise Exception('配置文件中未包含模型名：{}'.format(e))
    return model_name


def __get_data_range(params=None):
    if not params:
        params = parse_params()
    try:
        start_date = params['date_range']['start_date']
        end_date = params['date_range']['end_date']
    except Exception as e:
        raise Exception('配置文件中未包含时间区间：{}'.format(e))
    return str(start_date), str(end_date)


# def start_run(run_id: str = None, run_name: str = None, nested: str = None, tags: str = None):
#     if not get_use_cmo():
#         return
#     cmo_tracking.start_run(
#         run_id=run_id,
#         run_name=run_name,
#         nested=nested,
#         tags=tags)


class start_run(cmo_tracking.start_run):
    def __init__(
            self,
            run_id: str = None,
            run_name: str = None,
            nested: bool = False,
            tag = None
    ):
        if get_use_cmo():
            tags = {}
            tags['parent_run_id'] = '0'
            super(start_run, self).__init__(run_id=run_id, run_name=run_name, nested=nested, tags=tags, order=tag)

    def __enter__(self):
        if get_use_cmo():
            super(start_run, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if get_use_cmo():
            super(start_run, self).__exit__(exc_type, exc_val, exc_tb)


# def end_run():
#     if not get_use_cmo():
#         return
#     cmo_tracking.end_run()


def auto_log(task_type: str = None, **kwargs):
    if not get_use_cmo():
        return

    if not task_type:
        task_type = __get_model_name()
    if task_type not in ['sklearn', 'tensorflow',
                         'xgboost', 'lightgbm', 'pytorch', 'statsmodels', 'keras']:
        raise Exception(
            'task_type必须在sklearn,tensorflow,xgboost,lightgbm,pytorch,statsmodels,keras中')
    cmo_tracking.auto_log(task_type=task_type, **kwargs)


auto_log()


def log_params(params: dict):
    if not get_use_cmo():
        return
    __check_params('params', params)
    cmo_tracking.log_params(params, user_params=True)


def log_dataset(start_date, end_date, dataset_type='train'):
    if not get_use_cmo():
        return
    if dataset_type not in ['train', 'test']:
        raise Exception('dataset_type必须为train或test')
    start_date = str(start_date)
    end_date = str(end_date)
    config_start_date, config_end_date = __get_data_range()
    if len(start_date) != 8:
        raise Exception('开始时间格式错误:{}'.format(start_date))
    if len(end_date) != 8:
        raise Exception('结束时间格式错误:{}'.format(end_date))
    if end_date < start_date:
        raise Exception('开始时间大于结束时间')
    if start_date < config_start_date:
        raise Exception('开始时间小于样本区间开始时间')
    if end_date > config_end_date:
        raise Exception('结束时间大于样本区间结束时间')
    cmo_tracking.log_params({'start_date_{}'.format(dataset_type): start_date,
                             'end_date_{}'.format(dataset_type): end_date})


def log_metrics(metrics: dict, step: int = None):
    if not get_use_cmo():
        return
    if step and type(step) != int:
        raise Exception('step必须为int')
    __check_params('metrics', metrics)
    r_metrics = {}
    u_metrics = {}
    for k, v in metrics.items():
        if k in reserved_metrics:
            r_metrics[k] = v
        else:
            u_metrics[k] = v
    if r_metrics:
        cmo_tracking.log_metrics(r_metrics, step)
    if u_metrics:
        cmo_tracking.log_metrics(u_metrics, step, user_metrics=True)


def log_artifacts(local_file: str):
    if not get_use_cmo():
        return
    if not os.path.exists(local_file):
        raise Exception('文件{}不存在'.format(local_file))
    cmo_tracking.log_artifacts(local_file)
