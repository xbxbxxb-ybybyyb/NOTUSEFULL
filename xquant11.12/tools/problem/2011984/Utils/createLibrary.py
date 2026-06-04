from xquant.factordata import FactorData


def main():
    fd = FactorData()

    libraryName = "DynamicTriggers1000"
    factorNameList = ['Albest20170701', 'Model20190101_48', 'SeparateModelSignals', 'big_algo_20200801_0923', 'algo_20201101_20201123',
                      'ray_algo_20210201_20210324', 'ray_albest_20210701_20210912', 'ray_albest_20211101_20211116_order', 'ray_albest_20211101_20211116',
                      'ray_albest_20210701_20210912_VolumeAmp', 'ray_albest_20210701_20210912_Unknown', 'ray_albest_20210701_20210912_Reverse',
                      'ray_albest_20210701_20210912_PReverse', 'ray_albest_20210701_20210912_MomentumVAmp', "ray_albest_20211101_20211116",
                      "ray_albest_20211101_20211116_order", 'ray_albest_20211101_20211116_order_82',
                      'ray_albest_20211101_20211116_order_37', 'ray_albest_20211101_20211116_order', 'ray_albest_20211101_20211116_order_NonFFT']

    try:
        fd.create_factor_library(libraryName, "T+0")
    except Exception as e:
        print(e)

    for fn in factorNameList:
        try:
            fd.add_factor(libraryName, [fn])
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
