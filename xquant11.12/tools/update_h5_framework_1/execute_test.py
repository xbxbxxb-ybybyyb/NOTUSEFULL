from Wind.utils import *
xml_path = "config-h5.xml"
sql_config = get_sql_config(xml_path)
Modular = "barra_risk"
func = "execute"
md = __import__("Wind.%s" % Modular, fromlist=True)
f = getattr(md,func)
f(20131025,sql_config)


