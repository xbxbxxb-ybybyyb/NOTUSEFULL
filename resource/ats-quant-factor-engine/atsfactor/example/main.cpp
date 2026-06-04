#include "myfactor.h"

#include <fmt/format.h>
#include <huatai/atsquant/factor.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using fmt::println;
using huatai::atsquant::common::QuoteIndicator;
using namespace huatai::atsquant::factor;

int main() {
  // 因子管理器参数
  FactorManagerParam param{
      "foo",
      {
          json(FactorParam{"FactorActivePV"}),           //
          json(FactorParam{"FactorBOVwapGap"}),          //
          json(FactorParam{"FactorNSWBoll"}),            //
          json(FactorParam{"FactorNSWBuyDelDisToSell"}), //
          json(FactorParam{"FactorNSWTickPress"}),       //
      },
  };

  // 因子管理器
  auto fm = FactorManager::New(param).ValueOrDie();

  // 注册自定义因子类MyFactor
  auto st = FactorManager::RegisterFactor<MyFactor>();
  if (!st.ok()) {
    println("{}", st.ToString());
    return 1;
  }

  // 因子输出向量，顺序与参数列表指定的因子相同
  auto &values = fm->values(); // std::vector<double>

  // 传入行情
  QuoteIndicator quote{};
  st = fm->on_quote(quote);
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