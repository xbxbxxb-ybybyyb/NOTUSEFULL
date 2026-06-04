from xquant.xqutils.helper import multicore_init
import os
if not os.path.exists("/etc/.config/octopus/__xquant_config.py"):
    assert multicore_init()== True
