#include "huatai/atsquant/factor/factor_manager.h"

#include <chrono>
#include <gtest/gtest.h>

using namespace huatai::atsquant::factor;

TEST(Factor, TestAll) {
  MarketDataManagerOption option{};
  option.type = MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE;
  // std::string path = "/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine/dataset/"
  //  "688981.SH_20240617.parquet";
  std::string path = "./dataset/688012.SH_20240116.parquet";
  FactorManagerParam param{
      .factors =
          {
              json(FactorParam{.type = "FactorSecOrderBook"}),                                                  //
              json(FactorParam{.type = "FactorSecBuySellNum"}),                                                 //
              json(FactorParam{.type = "FactorSecTradeAgg"}),                                                   //
              json(FactorParam{.type = "FactorSellNumCorr3", .dependencies = {"FactorSecBuySellNum"}}),         //
              json(FactorParam{.type = "FactorBuyWillingByPrice", .dependencies = {"FactorSecTradeAgg"}}),      //
              json(FactorParam{.type = "FactorNSWSellMaxPriceCurCum", .dependencies = {"FactorSecOrderBook"}}), //
              json(FactorParam{.type = "FactorSeqNo"}),                                                         //
          },
      .sample_1s = true

  };
  param.num_threads = std::min(param.factors.size(), (size_t)8);

  auto fm = FactorManager::New(param, option).ValueOrDie();
  auto mdm = std::dynamic_pointer_cast<ParquetFileMarketDataManager>(MarketDataManager::Instance({}));
  ASSERT_NE(mdm, nullptr);
  auto st = mdm->set_path(path);
  ASSERT_TRUE(st.ok()) << st.ToString();
  for (auto re = mdm->next(); !mdm->is_end(); re = mdm->next()) {
    auto mdtime = mdm->default_manager()->get_mdtime();
    if (mdtime >= 9 * 3600 + 30 * 60) {
      // 9点30后开始计算
      st = fm->caculate();
      ASSERT_TRUE(st.ok()) << st.ToString();
    }
  }
}
