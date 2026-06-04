# ats-quant-factor-engine

## 依赖
- Arrow C++
- Parquet C++
- nlohmann json
- fmt
- pybind11

arrow + parquet rpm: https://htpan.htsc.com.cn/l/01uYfQ 

## 使用
```cpp
#include <fmt/format.h>
#include <huatai/atsquant/factor.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using fmt::println;
using huatai::atsquant::common::QuoteIndicator;
using huatai::atsquant::factor::FactorManager;
using huatai::atsquant::factor::MarketDataManager;
using huatai::atsquant::factor::MyFactor;

int main() {
  // 行情管理器
  auto mdm = std::make_shared<MarketDataManager>();

  // 因子列表参数，每一个列表项对应一个因子
  // 因子参数必须包含name，与因子中的name_成员对应。其他成员由因子自定义
  json param = R"([
    {
        "name": "dummy",
    },{
        "name": "ActivePriceVolume",
        "interval": 8,
        "price_spread": 0.05,
        "active_volume": 3000 
    },{
        "name": "my_factor",
        "int_param": -1
    }
  ])"_json;

  // 因子管理器
  auto fm = std::make_shared<FactorManager>(mdm, param);

  // 注册自定义因子类MyFactor
  auto st = fm->register_factor<MyFactor>();
  if (!st.ok()) {
    println("{}", st.ToString());
    return 1;
  }

  // 初始化参数列表中的因子
  // 这一步会通知因子管理器为每个因子分配输出地址、设置行情句柄等
  st = fm->init_factors();
  if (!st.ok()) {
    println("{}", st.ToString());
    return 1;
  }

  // 因子输出向量，顺序与参数列表指定的因子相同
  auto &values = fm->values(); // std::vector<double>

  // 传入行情
  QuoteIndicator quote{};
  st = mdm->on_quote(quote);
  if (!st.ok()) {
    println("{}", st.ToString());
    return 1;
  }

  // 触发计算
  st = fm->caculate();
  if (!st.ok()) {
    println("{}", st.ToString());
    return 1;
  }

  // 输出向量
  println("{}", json(values).dump());

  return 0;
}
```

## 构建
```
make
sudo make install # -> /usr/local
```

### configure
```
# 指定临时安装目录
make configure DESTDIR=build/package

# 安装到 /usr/local
make configure
```

### build
#### C++
```
make build JOBS=8
```

#### Python
todo

### install/package
```
make install
```

### clean
```
make clean
```

### 生成rpm
生成rpm所需的依赖:
- rpmdevtools
- rpmlint


```
make rpm
```