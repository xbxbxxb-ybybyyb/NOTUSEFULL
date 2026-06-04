//
// Created by zhangtian on 2023/5/23.
//

#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <iostream>

#include <sys/mman.h>
#include <sys/stat.h>
#include <cstdio>
#include <unistd.h>
#include "../thirdparty/zstd/lib/zstd.h"
#include <sys/mman.h>

#include "../include/xdb.h"

namespace huatai {
namespace strategy {
namespace xdb {

DataPack<Tick> huatai::strategy::xdb::Xdb::loadTickFull(const std::string &symbol, const std::string &date)
{
    return this->fetch<Tick>(symbol, date, Market_Data_Type_Tick_Full);
}

DataPack<Trade> Xdb::loadTrade(const std::string &symbol, const std::string &date)
{
    return this->fetch<Trade>(symbol, date, Market_Data_Type_Trade);
}

DataPack<OrderRecord> Xdb::loadOrder(const std::string &symbol, const std::string &date)
{
    return this->fetch<OrderRecord>(symbol, date, Market_Data_Type_Order);
}

DataPack<CancelOrder> Xdb::loadCancel(const std::string &symbol, const std::string &date)
{
    return this->fetch<CancelOrder>(symbol, date, Market_Data_Type_Cancel);
}

DataPack<Status> Xdb::loadStatus(const std::string &symbol, const std::string &date)
{
    return this->fetch<Status>(symbol, date, Market_Data_Type_Status);
}

DataPack<Quote> Xdb::loadTickEx(const std::string &symbol, const std::string &date)
{
    return this->fetch<Quote>(symbol, date, Market_Data_Type_Tick_Ex);
}

DataPack<Tick> Xdb::loadTick1s(const std::string &symbol, const std::string &date)
{
    return this->fetch<Tick>(symbol, date, Market_Data_Type_Tick_1s);
}

DataPack<KLine1Min> Xdb::loadKLine1min(const std::string &symbol, const std::string &date)
{
    return this->fetch<KLine1Min>(symbol, date, Market_Data_Type_KLine1Min);
}

DataPack<Daily> Xdb::loadDaily(const std::string &symbol, const std::string &date)
{
    bool isSH = symbol.ends_with(".SH");
    std::string market = isSH ? "SH" : "SZ";

    std::string path = this->dataRootPath + getFilePath(date, market, Market_Data_Type_Daily);

    struct stat buffer;
    if (stat(path.c_str(), &buffer) != 0)
    {
        path = this->dataRootPath + getFilePath(date, market, Market_Data_Type_Daily);
    }

    auto itr = this->fileLoaderMap.find(path);
    FileLoader *loader;
    if (itr == this->fileLoaderMap.end())
    {
        loader = new FileLoader(Market_Data_Type_Daily, path, false);
    }
    else
    {
        loader = itr->second;
    }
    return loader->loadSymbolDailyData(date, symbol);
}

std::pair<std::vector<std::string>, std::vector<Factor>> Xdb::loadFactor(
    const std::string &table, const std::string &symbol, const std::string date)
{
    std::string path = getFactorFilePath(table, date, symbol);
    auto itr = this->fileLoaderMap.find(path);
    FileLoader *loader;
    if (itr == this->fileLoaderMap.end())
    {
        loader = new FileLoader(Market_Data_Type_Factor, path, false);
    }
    else
    {
        loader = itr->second;
    }
    return loader->loadFactor(symbol, date);
}


std::unordered_set<std::string> Xdb::get_all_symbol_by_type(const std::string& market_str, const std::string &date, MarketDataType type)
{
    std::string path = this->dataRootPath + getFilePath(date, market_str, type);
    struct stat buffer;
    if (stat(path.c_str(), &buffer) != 0)
    {
        path = this->dataRootPath + getFilePath(date, market_str, type);
    }
    auto itr = this->fileLoaderMap.find(path);
    FileLoader *loader;
    if (itr == this->fileLoaderMap.end())
    {
        loader = new FileLoader(type, path, false);
        this->fileLoaderMap.emplace(path, loader);
    }
    else
    {
        loader = itr->second;
    }
    auto res = loader->get_symbol_set();
    return res;
}


std::unordered_map<int, std::vector<std::string>> Xdb::get_all_symbol_by_channel(const std::string& market_str, const std::string &date, MarketDataType type)
{
    std::string path = this->dataRootPath + getFilePath(date, market_str, type);
    struct stat buffer;
    if (stat(path.c_str(), &buffer) != 0)
    {
        path = this->dataRootPath + getFilePath(date, market_str, type);
    }
    auto itr = this->fileLoaderMap.find(path);
    FileLoader *loader;
    if (itr == this->fileLoaderMap.end())
    {
        loader = new FileLoader(type, path, false);
        this->fileLoaderMap.emplace(path, loader);
    }
    else
    {
        loader = itr->second;
    }

    auto res = loader->get_channel_map();

    return res;
}

template<typename T>
DataPack<T> Xdb::fetch(const std::string &symbol, const std::string &date, MarketDataType type)
{
    bool isSH = symbol.ends_with(".SH");
    std::string market = isSH ? "SH" : "SZ";

    std::string path = this->dataRootPath + getFilePath(date, market, type);
    struct stat buffer;
    if (stat(path.c_str(), &buffer) != 0)
    {
        path = this->dataRootPath + getFilePath(date, market, type);
    }
    auto itr = this->fileLoaderMap.find(path);
    FileLoader *loader;
    if (itr == this->fileLoaderMap.end())
    {
        loader = new FileLoader(type, path, false);
        this->fileLoaderMap.emplace(path, loader);
    }
    else
    {
        loader = itr->second;
    }
    
    return loader->loadSymbol<T>(date, symbol);
}

std::string Xdb::getFilePath(const std::string &date, const std::string &market, MarketDataType type)
{

    std::string path = "/00_MarketData/00_StockData/02_UHFData/";

    if (market == "SZ")
    {
        path += "00_SZ/";
    }
    else if (market == "SH")
    {
        path += "01_SH/";
    }

    if (type == Market_Data_Type_Order)
    {
        path += "02_Order/";
    }
    else if (type == Market_Data_Type_Trade)
    {
        path += "01_Trade/";
    }
    else if (type == Market_Data_Type_Cancel)
    {
        path += "03_Cancel/";
    }
    else if (type == Market_Data_Type_Tick_1s)
    {
        path += "04_Tick1s/";
    }
    else if (type == Market_Data_Type_Tick_Full)
    {
        path += "05_TickFull/";
    }
    else if (type == Market_Data_Type_Tick_Ex)
    {
        path += "00_TickEx/";
    }
    else if (type == Market_Data_Type_Daily)
    {
        path += "08_DailyData/";
    }
    else if (type == Market_Data_Type_KLine1Min)
    {
        path += "06_KLine1Min/";
    }
    else if (type == Market_Data_Type_Status) {
        path += "09_Status/";
    }

    path += date + "/" + "Stock_" + market + "_";

    if (type == Market_Data_Type_Order)
    {
        path += "Order_";
    }
    else if (type == Market_Data_Type_Trade)
    {
        path += "Trade_";
    }
    else if (type == Market_Data_Type_Cancel)
    {
        path += "Cancel_";
    }
    else if (type == Market_Data_Type_Tick_1s)
    {
        path += "Tick1s_";
    }
    else if (type == Market_Data_Type_Tick_Full)
    {
        path += "TickFull_";
    }
    else if (type == Market_Data_Type_Tick_Ex)
    {
        path += "TickEx_";
    }
    else if (type == Market_Data_Type_Daily)
    {
        path += "DailyData_";
    }
    else if (type == Market_Data_Type_KLine1Min)
    {
        path += "KLine1Min_";
    }
    else if (type == Market_Data_Type_Status) {
        path += "Status_";
    }

    path += date;

    return path;
}

std::string Xdb::getFactorFilePath(const std::string &table, const std::string &date, const std::string &symbol)
{
    return this->dataRootPath + "/01_FactorData/00_T0/" + table + "/" + date + "/" + symbol;
    // return "/dfs/group/900001/XDB/01_FactorData/00_T0/" + table + "/" + date + "/" + symbol;
    // return "/dfs/user/018083/00_T0/" + table + "/" + date + "/" + symbol;
}

bool FileLoader::openFile(const std::string &path)
{
    this->fd = open(path.c_str(), O_RDONLY);
    if (this->fd < 0)
    {
        failed = true;
        printf("open file failed errorno = %s, path = %s\n", strerror(errno), path.c_str());
        return false;
    }

    struct stat statBuf;
    fstat(fd, &statBuf);

    this->fileSize = statBuf.st_size;
    return true;
}

bool FileLoader::loadFileMetaData()
{
    if (this->failed)
    {
        return false;
    }
    if (this->type == Market_Data_Type_Daily)
    {
        return true;
    }
    metaData.parseHeader(this->fd);

    const auto& location_map = metaData.getLocationMap();

    for (const auto& kv : location_map)
    {
        symbol_set.insert(kv.first);

        auto it = channel_symbols_map.find(kv.second.channel);
        if (it != channel_symbols_map.end())
        {
            it->second.emplace_back(kv.first);
        }
        else
        {
            std::vector<std::string> symbols;
            symbols.emplace_back(kv.first);
            channel_symbols_map.emplace(kv.second.channel, symbols);
        }
    }
    return true;
}

template<typename T>
DataPack<T> FileLoader::loadSymbol(const std::string &date, const std::string &symbol)
{
    auto &location = this->metaData.getLocation(symbol.substr(0, 6));
    if (location.start == 0)
    {
        return DataPack<T>(0, 0);
    }

    int64_t start = location.start;
    int64_t end = location.end;

    lseek64(fd, start, SEEK_SET);

    char *tmp = new char[end - start];
    size_t size = read(fd, tmp, end - start);

    unsigned long long const rSize = ZSTD_getFrameContentSize(tmp, end - start);
    void *buff = malloc(rSize);
    size_t const dSize = ZSTD_decompress(buff, rSize, tmp, end - start);

    if (dSize < 0)
    {
        printf("zstd decompress error %lu", dSize);
    }
    int64_t count = rSize / this->itemSize;
    T *t = (T *)buff;
    return DataPack<T>(t, count);
}

DataPack<Daily> FileLoader::loadSymbolDailyData(const std::string &date, const std::string &symbol)
{
    void *mapped = mmap(nullptr, fileSize, PROT_READ, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED)
    {
        printf("mmap file failed, errorno = %s, path = %s", strerror(errno), path.c_str());
        return DataPack<Daily>(0, 0);
    }
    Daily *daily = reinterpret_cast<Daily *>(mapped);
    int64_t itemSize = fileSize / sizeof(Daily);
    for (int i = 0; i < itemSize; i++)
    {
        if (memcmp((void *)symbol.c_str(), (void *)daily[i].security_id, 6) == 0)
        {
            // 找到目标, 内存可能会泄漏，如果使用方不释放
            Daily *tmp = new Daily;
            memcpy((void *)tmp, (void *)(&daily[i]), sizeof(Daily));
            return DataPack<Daily>(tmp, 1);
        }
    }
    return DataPack<Daily>(0, 0);
}

std::pair<std::vector<std::string>, std::vector<Factor>> FileLoader::loadFactor(const std::string &symbol, const std::string date)
{
    auto &location = this->metaData.getLocation(symbol.substr(0, 6));
    if (location.start == 0)
    {
        return std::pair(std::vector<std::string>(), std::vector<Factor>());
    }

    std::vector<std::string> factorColArray;
    std::vector<Factor> factorValueArray;

    int64_t start = location.start;
    int64_t end = location.end;
    lseek64(fd, 16 + this->metaData.getHeaderSize(), SEEK_SET);
    size_t cl = start - 16 - this->metaData.getHeaderSize();
    char *tmp = new char[cl + 1];
    read(fd, tmp, cl);
    tmp[cl] = '\0';
    std::string colArray = tmp;

    // 按照逗号进行分割
    {
        size_t q = 0;
        auto p = colArray.find_first_of(",", q);
        while (true)
        {
            std::string n = colArray.substr(q, p - q);
            factorColArray.push_back(n);
            q = p + 1;
            p = colArray.find_first_of(",", q);
            // 还有最后一个分段
            if (p == std::string::npos)
            {
                std::string n = colArray.substr(q, colArray.size() - q);
                factorColArray.push_back(n);
                break;
            }
        }
    }

    delete tmp;
    lseek64(fd, start, SEEK_SET);

    char *valueTmp = new char[end - start];
    read(fd, valueTmp, end - start);

    unsigned long long const rSize = ZSTD_getFrameContentSize(valueTmp, end - start);
    void *buff = malloc(rSize);
    size_t const dSize = ZSTD_decompress(buff, rSize, valueTmp, end - start);

    if (dSize < 0)
    {
        printf("zstd decompress error %lu", dSize);
    }

    double *valueArray = (double *)buff;
    int factorCount = factorColArray.size();
    int index = 0;
    int64_t doubleSize = sizeof(double);
    while (index * doubleSize < rSize)
    {
        Factor factor;
        int64_t pointStart = (int64_t)(void *)valueArray + index * doubleSize;
        for (int i = 0; i < factorCount; i++)
        {
            if (i == 0)
            {
                factor.applSeqNum = *((int64_t *)pointStart);
            }
            else
            {
                factor.values.push_back(*(double *)(pointStart + i * doubleSize));
            }
        }
        factorValueArray.push_back(factor);
        index += factorCount;
    }

    return std::pair<std::vector<std::string>, std::vector<Factor>>(factorColArray, factorValueArray);
}

void MetaData::parseHeader(int fd)
{
    lseek(fd, 8, SEEK_SET);
    read(fd, &this->headerSize, sizeof(int64_t));
    this->headerCount = this->headerSize / sizeof(HeaderItem);
    HeaderItem item[this->headerCount];
    read(fd, item, headerSize);
    for (int i = 0; i < this->headerCount; i++)
    {
        this->locationMap[item[i].symbol] = item[i];
    }
}

int64_t MetaData::getHeaderSize()
{
    return this->headerSize;
}

const HeaderItem &MetaData::getLocation(const std::string &symbol)
{
    auto itr = this->locationMap.find(symbol);
    if (itr == this->locationMap.end())
    {
        return this->empty;
    }
    else
    {
        return itr->second;
    }
}
} // namespace xdb
} // namespace strategy
} // namespace huatai