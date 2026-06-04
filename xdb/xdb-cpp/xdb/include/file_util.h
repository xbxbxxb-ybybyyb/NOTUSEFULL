//
// Created by appadmin on 2023/3/1.
//

#ifndef EVENTDRIVENSTRATEGY_FILE_UTIL_H
#define EVENTDRIVENSTRATEGY_FILE_UTIL_H

#include <string>

#include <cstdio>
#include <unistd.h>

namespace huatai {
namespace strategy {
namespace xdb {

class FileUtil {
public:
  static inline uint32_t ReadFileContent(const char *filename, std::string &content) {
    if (!Exists(filename)) {
      printf("file not exists %s", filename);
      return -1;
    }
    FILE *f = fopen(filename, "rb");
    fseek(f, 0, SEEK_END);
    uint32_t length = ftell(f);
    content.resize(length);
    fseek(f, 0, 0);
    fread((void *) content.data(), sizeof(char), length, f);
    fclose(f);
    printf("file load %s", filename);
    return length;
  }

  static inline bool Exists(const char *filename) {
    return access(filename, 0) == 0;
  }
};

} // namespace eventdriven
} // namespace strategy
} // namespace huatai
#endif // EVENTDRIVENSTRATEGY_FILE_UTIL_H
