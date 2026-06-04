//
// Created by zhangtian on 2023/6/6.
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
#include "../include/file_util.h"
#include "cmath"

namespace huatai {
namespace strategy {
namespace xdb {

int zstdCompress(const char *src, size_t srcLen, char *dest, size_t destLen)
{
    double x = NAN;
    /* Compress.
     * If you are doing many compressions, you may want to reuse the context.
     * See the multiple_simple_compression.c example.
     */
    size_t const cSize = ZSTD_compress((void *)dest, destLen, (void *)src, srcLen, 1);
    return cSize;
}

// int Xdb::loadFactor() {
//     std::string path = "/data/user/020063/factor_data/sappe/20230101/000001.SZ";
//     int fd = open(path.c_str(), O_RDONLY);
//     struct stat statBuf;
//     fstat(fd, &statBuf);
//
//     int64_t size = statBuf.st_size;
//
//     void *mapped = mmap(nullptr, size, PROT_READ, MAP_SHARED, fd, 0);
//     if (mapped == MAP_FAILED)
//     {
//         return false;
//     }
//
//
//     char tmp[size];
//     memcpy(tmp, mapped, size);
//
//     int start = ((int*)((char*)tmp + 8 + 8 + 8))[0];
//     int end = ((int*)((char*)tmp + 8 + 8 + 8 + 8))[0];
//
//
//     char factorName[start - (8 + 8 + 24)];
//     memcpy(factorName, (void*)(((int64_t)mapped) + 8 + 8 + 24), start - (8 + 8 + 24));
//
//
//     char uncompress[end - start];
//     memcpy(uncompress, (void*)(((int64_t)mapped) + start), end - start);
//
//     unsigned long long const rSize = ZSTD_getFrameContentSize(uncompress, end - start);
//     char buff[rSize];
//     size_t const dSize = ZSTD_decompress(buff, rSize, uncompress, end - start);
//
//     if (dSize < 0)
//     {
//         printf("zstd decompress error %d", dSize);
//     }
//     int dd = 1;
//
// }
int Xdb::updateFactor(const std::string &table, const std::string &symbol, const std::string date,
    const std::vector<std::string> &factorNames, const std::vector<Factor> &factorValues)
{

    std::string path = this->getFactorFilePath(table, date, symbol);

    if (!FileUtil::Exists(path.c_str()))
    {
        return saveFactor(table, symbol, date, factorNames, factorValues);
    }

    auto oldFactor = this->loadFactor(table, symbol, date);

    // 进行合并，新因子直接增加，旧因子进行修改

    std::vector<std::string> &oldFactorNames = oldFactor.first;
    std::vector<Factor> &oldFactorValues = oldFactor.second;

    for (int newColNameIndex = 0; newColNameIndex < factorNames.size(); newColNameIndex++)
    {
        // 第一列是 appselNum，所以跳过
        if (newColNameIndex == 0)
        {
            continue;
        }
        std::string colName = factorNames[newColNameIndex];
        int oldColNameIndex = -1;
        for (int i = 0; i < oldFactorNames.size(); i++)
        {
            if (colName == oldFactorNames[i])
            {
                oldColNameIndex = i;
                break;
            }
        }

        if (oldColNameIndex != -1)
        {
            // 老因子，更新因子值
            for (int i = 0; i < oldFactorValues.size(); i++)
            {
                Factor &oldFactor = oldFactorValues[i];
                const Factor &newFactor = factorValues[i];
                oldFactor.values[oldColNameIndex - 1] = newFactor.values[newColNameIndex - 1];
            }
        }
        else
        {
            // 新因子，增加因子值
            oldFactorNames.push_back(colName);
            for (int i = 0; i < oldFactorValues.size(); i++)
            {
                Factor &oldFactor = oldFactorValues[i];
                const Factor &newFactor = factorValues[i];
                oldFactor.values.push_back(newFactor.values[newColNameIndex - 1]);
            }
        }
    }

    return saveFactor(table, symbol, date, oldFactorNames, oldFactorValues);
}

int Xdb::saveFactor(const std::string &table, const std::string &symbol, const std::string date,
    const std::vector<std::string> &factorNames, const std::vector<Factor> &factorValues)
{

    // TODO: table及上级目录最好在并发执行C++代码前就创建出来，C++代码不做目录结构的创建
    std::string path = this->getFactorFilePath(table, date, symbol);

    char magic[4];
    magic[0] = '1';
    magic[1] = '2';
    magic[2] = '3';
    magic[3] = '4';

    char remain[4];
    remain[0] = '1'; // version
    remain[1] = '5'; // type
    remain[2] = '0';
    remain[3] = '0';

    // 写入
    int tickfull_fd = open(path.c_str(), O_RDWR | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
    char emptyChar = '\0';
    char dotChar = ',';
    {
        // write block
        write(tickfull_fd, magic, 4 * sizeof(char));
        write(tickfull_fd, remain, 4 * sizeof(char));

        /**
         *
         * char[9] int64_t start end int64_t
         *
         */
        char symbol1[8];
        int symbolSize = sizeof(symbol1);

        int int64Size = sizeof(int64_t);
        int64_t headerItemSize = symbolSize + int64Size * 2 + sizeof(int16_t);
        // 一只文件只有一个股票的，所以直接乘以1
        int64_t headerSize = headerItemSize * 1;
        write(tickfull_fd, &headerSize, sizeof(int64_t));

        int64_t factorNamesLen = 0;
        int64_t factorNameStart = 8 + 8 + headerSize;
        lseek64(tickfull_fd, factorNameStart, SEEK_SET);
        for (int i = 0; i < factorNames.size(); i++)
        {
            std::string name = factorNames[i];
            int64_t nameLen = name.length();
            write(tickfull_fd, name.c_str(), nameLen);
            if (i != factorNames.size() - 1)
            {
                write(tickfull_fd, &dotChar, 1);
                nameLen += 1;
            }
            factorNamesLen += nameLen;
        }

        int64_t headerCurrentIndex = 8 + 8;
        // 因子名称放在 header 和 body之间，所以初始的start需要修改
        int64_t start = 8 + 8 + headerSize + factorNamesLen;
        int64_t end = 0;


        int64_t factorValueLen = 0;
        int64_t factorValueLenSum = 0;
        int64_t doubleSize = sizeof(double);

        for (auto itr = factorValues.begin(); itr != factorValues.end(); itr++)
        {
            factorValueLen = int64Size + doubleSize * itr->values.size();
            factorValueLenSum += factorValueLen;
        }

        void *tmp = malloc(factorValueLenSum);
        //        char tmp[factorValueLenSum];
        int64_t factorIndex = 0;
        for (auto itr = factorValues.begin(); itr != factorValues.end(); itr++)
        {
            int64_t pointStart = (int64_t)tmp + factorIndex * factorValueLen;
            std::memcpy((void *)(pointStart), &itr->applSeqNum, int64Size);
            int index = 0;
            for (double val : itr->values)
            {
                std::memcpy((void *)(pointStart + int64Size + index * doubleSize), &val, doubleSize);
                index++;
            }
            factorIndex++;
        }

        size_t const cBuffSize = ZSTD_compressBound(factorValueLenSum);
        char *compressed = (char *)malloc(cBuffSize);
        memset(compressed, 0, cBuffSize);
        int compress_size = zstdCompress((const char *)tmp, factorValueLenSum, compressed, cBuffSize);
        if (compress_size <= 0)
        {
            printf("compress error.\n");
            printf("%s\n", strerror(errno));
            return -1;
        }

        end = start + compress_size;
        lseek64(tickfull_fd, 8 + 8, SEEK_SET);
        write(tickfull_fd, symbol.c_str(), symbolSize - 2);
        write(tickfull_fd, &emptyChar, 1);
        write(tickfull_fd, &emptyChar, 1);
        int16_t channel = 0;
        write(tickfull_fd, &channel, sizeof(int16_t));
        write(tickfull_fd, &start, int64Size);
        write(tickfull_fd, &end, int64Size);

        headerCurrentIndex += headerItemSize;
        lseek64(tickfull_fd, start, SEEK_SET);
        write(tickfull_fd, compressed, compress_size);
        lseek64(tickfull_fd, headerCurrentIndex, SEEK_SET);
        delete compressed;
        free(tmp);
        start = end;
        close(tickfull_fd);
        return 0;
    }
}

} // namespace xdb
} // namespace strategy
} // namespace huatai