from xquant.factordata import FactorData


def createLibrary(libraryName):
    fd = FactorData()

    try:
        fd.create_factor_library(libraryName, "T+0")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    # TODO
    outputLibrary = "CBFactorDevLib"
    createLibrary(outputLibrary)
