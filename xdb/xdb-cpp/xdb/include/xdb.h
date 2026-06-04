//
// Created by zhangtian on 2023/5/23.
//

#pragma once

#include "market_types.h"
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include "factor.h"

namespace huatai {
namespace strategy {
namespace xdb {

template<typename T>
class DataPack
{
public:
    DataPack(T *data, int64_t size)
        : data(data)
        , size(size)
    {}
    T *data;
    int64_t size;
};

#pragma pack(1)
struct HeaderItem
{
    char symbol[8];
    int16_t channel;
    int64_t start;
    int64_t end;
};
#pragma pack()

class MetaData
{
public:
    MetaData()
    {
        memset(&empty, 0, sizeof(HeaderItem));
    }
    const HeaderItem &getLocation(const std::string &symbol);
    void parseHeader(int fd);
    int64_t getHeaderSize();

    const std::unordered_map<std::string, HeaderItem>& getLocationMap() const { return locationMap; }

private:
    int version;
    MarketDataType type;
    std::unordered_map<std::string, HeaderItem> locationMap;
    int64_t headerSize;
    int64_t headerCount;
    HeaderItem empty;
};

class FileLoader
{
public:
    FileLoader(MarketDataType type, std::string &path, bool cached)
        : type(type)
        , path(path)
    {
        if (type == Market_Data_Type_Order)
        {
            this->itemSize = sizeof(OrderRecord);
        }
        else if (type == Market_Data_Type_Trade)
        {
            this->itemSize = sizeof(Trade);
        }
        else if (type == Market_Data_Type_Cancel)
        {
            this->itemSize = sizeof(CancelOrder);
        }
        else if (type == Market_Data_Type_Tick_1s)
        {
            this->itemSize = sizeof(Tick);
        }
        else if (type == Market_Data_Type_Tick_Full)
        {
            this->itemSize = sizeof(Tick);
        }
        else if (type == Market_Data_Type_Tick_Ex)
        {
            this->itemSize = sizeof(Quote);
        }
        else if (type == Market_Data_Type_KLine1Min)
        {
            this->itemSize = sizeof(KLine1Min);
        }
        else if (type == Market_Data_Type_Status)
        {
            this->itemSize = sizeof(Status);
        }
        this->openFile(path);
        this->loadFileMetaData();
    }
    template<typename T>
    DataPack<T> loadSymbol(const std::string &date, const std::string &symbol);
    DataPack<Daily> loadSymbolDailyData(const std::string &date, const std::string &symbol);
    std::pair<std::vector<std::string>, std::vector<Factor>> loadFactor(const std::string &symbol, const std::string date);

    const std::unordered_set<std::string> get_symbol_set() const { return symbol_set; }
    const std::unordered_map<int, std::vector<std::string>> get_channel_map() const { return channel_symbols_map; }
private:
    std::vector<OrderRecord> parseOrder(const std::string date, const std::string symbol);

private:
    bool openFile(const std::string &path);
    bool loadFileMetaData();

private:
    std::string path;
    MarketDataType type;
    int64_t fileSize;
    int64_t itemSize;
    MetaData metaData;
    int fd;
    bool failed = false;

    std::unordered_set<std::string> symbol_set;
    std::unordered_map<int, std::vector<std::string>> channel_symbols_map;  // channel -> [symbol1, symbol2, symbol3]
};

class Xdb
{

public:
    Xdb(){};
    Xdb(std::string root)
        : dataRootPath(root){};
    ~Xdb(){};
    DataPack<Daily> loadDaily(const std::string &symbol, const std::string &date);
    DataPack<Trade> loadTrade(const std::string &symbol, const std::string &date);
    DataPack<OrderRecord> loadOrder(const std::string &symbol, const std::string &date);
    DataPack<CancelOrder> loadCancel(const std::string &symbol, const std::string &date);
    DataPack<Status> loadStatus(const std::string &symbol, const std::string &date);
    DataPack<Tick> loadTickFull(const std::string &symbol, const std::string &date);
    DataPack<Quote> loadTickEx(const std::string &symbol, const std::string &date);
    DataPack<Tick> loadTick1s(const std::string &symbol, const std::string &date);
    DataPack<KLine1Min> loadKLine1min(const std::string &symbol, const std::string &date);
    std::pair<std::vector<std::string>, std::vector<Factor>> loadFactor(
        const std::string &table, const std::string &symbol, const std::string date);

public:
    int saveFactor(const std::string &table, const std::string &symbol, const std::string date, const std::vector<std::string> &factorNames,
        const std::vector<Factor> &factorValues);
    int updateFactor(const std::string &table, const std::string &symbol, const std::string date,
        const std::vector<std::string> &factorNames, const std::vector<Factor> &factorValues);
    //    int loadFactor();
    std::unordered_set<std::string> get_all_symbol_by_type(const std::string& market_str, const std::string &date, MarketDataType type);
    const std::unordered_set<std::string>& get_symbol_set() const { return symbol_set; }

    std::unordered_map<int, std::vector<std::string>> get_all_symbol_by_channel(const std::string& market_str, const std::string &date, MarketDataType type);
private:
    template<typename T>
    DataPack<T> fetch(const std::string &symbol, const std::string &date, MarketDataType type);
    std::string getFilePath(const std::string &date, const std::string &market, MarketDataType type);
    std::string getFactorFilePath(const std::string &table, const std::string &date, const std::string &symbol);

private:
    std::unordered_map<std::string, FileLoader *> fileLoaderMap;
    std::string shm_path = "/dev/shm/";
    std::string dataRootPath = "/dfs/group/900001/XDB/";

    std::unordered_set<std::string> symbol_set;
};

} // namespace xdb
} // namespace strategy
} // namespace huatai