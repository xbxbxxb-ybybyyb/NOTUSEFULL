from xquant.model.tracking import parse_params, log_params

def log_yaml_params(yaml_path):
    project_config = parse_params(yaml_path)
    # 上传任务参数
    yaml_params = {}
    for outer_key, outer_value in project_config.items():
        for inner_key, inner_value in outer_value.items():
            if inner_key == "model_params":
                for key in inner_value:
                    yaml_params['{}.{}'.format("model_params", key)] = inner_value[key]
            if inner_key == "data_params":
                for key in inner_value:
                    yaml_params['{}.{}'.format("data_params", key)] = inner_value[key]
            if inner_key == "task_params":
                for key in inner_value:
                    yaml_params['{}.{}'.format("task_params", key)] = inner_value[key]
            if inner_key in ["start_date", "end_date"]:
                yaml_params[inner_key] = inner_value
    print("project yaml content:", yaml_params)
    log_params(yaml_params)
    return


