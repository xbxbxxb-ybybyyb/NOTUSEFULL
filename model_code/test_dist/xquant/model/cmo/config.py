import os

import yaml

config_file = "cmo_config.yaml"
config = yaml.full_load(
    open(os.path.join(os.path.dirname(__file__), "basic_configure.yaml"), "r", encoding="utf8").read()
)
extra_config = {}
if os.path.exists(config_file):
    extra_config = yaml.full_load(open(config_file, "r", encoding="utf8").read())
config.update(extra_config)


class AutoLogStatus:
    ACTIVE = "Active"
    INACTIVE = "InActive"

    @classmethod
    def active(cls):
        os.environ["AutoLog"] = AutoLogStatus.ACTIVE

    @classmethod
    def inactive(cls):
        os.environ["AutoLog"] = AutoLogStatus.INACTIVE

    @classmethod
    def is_active(cls):
        if os.environ.get("AutoLog") == AutoLogStatus.ACTIVE:
            return True
        return False
