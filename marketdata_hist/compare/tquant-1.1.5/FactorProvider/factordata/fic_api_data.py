from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig
from FactorProvider.conf import DubboConf
import json
import pandas as pd


class FicApiData:

    def __init__(self):
        self.fic_status_dict = {1: '操作成功',
                                -1: '资源不存在',
                                -2: '返回字段信息未配置',
                                -3: '检索字段不合法',
                                -4: '返回字段不合法',
                                -5: '排序字段不合法',
                                -6: '检索key值不存在',
                                -7: 'key未关联此接口',
                                -9: '查询数据发生异常'}

    def get_fic_api_data(self, resource, paramMaps, selectedFields="", startrow=0, rownum=1000, orderBy=""):
        """
        通过dubbo接口查询资讯数据
        :param key: apikey
        :param resource: 资源名称，str，表名
        :param paramMaps: 查询参数，dict，需根据表名确认可传参数，key:value均为string类型
        :param selectedFields: 查询字段，str，多个字段需用逗号隔开，为空则查询全部字段，
        :param startrow: 分页偏移，int，默认0
        :param rownum: 每页条数，int，默认1000
        :param orderBy: 排序字段，str，按所传字段升序排序
        :return:
        """
        # key = "cfd257c9d12542eb86105c341d27fec9"

        # dubbo配置
        resourceData_service_interface = 'com.htsc.xquant.dataagent.service.dubbo.ZxNewsInfoService'
        resourceData_config = ApplicationConfig(DubboConf.DUBBO_APPLICATIONCONFIG_UTILS)
        config_registry = ZookeeperRegistry(DubboConf.DUBBO_CONFIG_IP, resourceData_config)

        resourceData = DubboClient(resourceData_service_interface, config_registry, version=DubboConf.version)

        json_str = json.dumps(paramMaps)
        get_result = resourceData.getResourceData(resource, json_str, startrow, rownum, orderBy,
                                                  selectedFields)
        # print(get_result)
        result = json.loads(get_result)
        status = result.get('status')
        if status == 1:
            data = result['dataList']
            df = pd.DataFrame(data)
            final_result = {"totalCount": result["totalCount"], "data": df}
            return final_result
        else:
            raise Exception("dubbo接口获取数据异常：{0}".format(self.fic_status_dict[status]))


if __name__ == "__main__":
    # resource = "ZX_FNDNETASSETVAL"
    # paramMaps = {"ENDDATE": "[2013-07-29,2015-07-29]", "TRADINGCODE": "310358"}# 650002
    # selectedFields = ""
    # orderBy = "CHANGERATE"
    # rownum = 1000
    # startrow = 0

    # resource = "ZX_FNDMANAGER"
    # paramMaps = {"TRADINGCODE": "310358"}#650002
    # selectedFields = ""
    # orderBy = ""
    # rownum = 1000
    # startrow = 0

    resource = "ZX_PUBSECURITIESMAIN"
    paramMaps = {"LISTINGSTATECODE": '1'}
    selectedFields = ""
    orderBy = ""
    rownum = 2000
    startrow = 0

    fad = FicApiData()
    df = fad.get_fic_api_data(resource, paramMaps, selectedFields, startrow=startrow, rownum=rownum, orderBy=orderBy)
    print(df)
