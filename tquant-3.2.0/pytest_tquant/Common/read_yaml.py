import yaml


def read_yaml(filename):
    with open(filename, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


if __name__ == "__main__":
    print(read_yaml('conf.yaml'))
