import psutil

try:
    from .setEnv import sysFlag

    if sysFlag != "big_data":
        from .storage.sql_config_ini import write_provider_ini, file_time_interval

        # print("file_time_interval:", file_time_interval())
        if file_time_interval() > 1200:
            p = psutil.Process()
            if 'ray' in ",".join(p.cmdline()):
                pass
            else:
                write_provider_ini()

except Exception as e:
    import traceback

    print(traceback.print_exc())
    print('mysql_conf.ini updated failed! {0}'.format(e))
    pass
