#include "huatai/atsquant/factor/market_data_manager.h"

#include <gtest/gtest.h>

using namespace huatai::atsquant::factor;

std::shared_ptr<ParquetFileMarketDataManager> pq_mdm_;
std::shared_ptr<SingleMarketDataManager> mdm_;

template <typename ParamType> class MarketDataManagerTest : public testing::TestWithParam<ParamType> {
protected:
  MarketDataManagerTest() {
    if (mdm_ != nullptr) {
      return;
    }

    MarketDataManagerOption option{.type = MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE};
    std::string path = "dataset/688012.SH_20240116.parquet";
    pq_mdm_ = std::dynamic_pointer_cast<ParquetFileMarketDataManager>(MarketDataManager::Instance(option));
    if (pq_mdm_ == nullptr) {
      throw std::runtime_error("Can't create ParquetFileMarketDataManager");
    }

    auto st = pq_mdm_->set_path(path);
    if (!st.ok()) {
      throw std::runtime_error(st.ToString());
    }

    for (auto re = pq_mdm_->next(); re.ok(); re = pq_mdm_->next())
      ;

    mdm_ = pq_mdm_->default_manager();
  }

  void SetUp() override { pq_mdm_->reset(); }
};

struct GetPrevNParam {
  int64_t init_index = 0;
  int64_t n = 0;
  int64_t size = 0;
};

using GetPrevNTest = MarketDataManagerTest<GetPrevNParam>;

TEST_P(GetPrevNTest, get_prev_n) {
  const auto &param = GetParam();
  pq_mdm_->set_num_quote(param.init_index);
  auto index = mdm_->get_prev_n(mdm_->get_num_quote(), param.n);
  ASSERT_EQ(mdm_->get_num_quote() - index, param.size);
}

INSTANTIATE_TEST_SUITE_P(MarketData, GetPrevNTest,
                         testing::ValuesIn(std::vector<GetPrevNParam>{/* begin */
                                                                      {0, 10, 0},
                                                                      {5, 3, 3},
                                                                      {100, 200, 100},
                                                                      {100, 100, 100},
                                                                      {100, 1, 1}
                                                                      /* end */}));

struct GetPrevNSecParam {
  int64_t init_index = 0;
  int64_t n_sec = 0;
  int64_t expected = 0;
};

using GetPrevNSecTest = MarketDataManagerTest<GetPrevNSecParam>;

TEST_P(GetPrevNSecTest, get_prev_n_sec) {
  const auto &param = GetParam();
  pq_mdm_->set_num_quote(param.init_index);
  auto tv = mdm_->get_prev_n_sec_quote(param.n_sec);
  ASSERT_EQ(tv.row_index, param.expected);
}

INSTANTIATE_TEST_SUITE_P(MarketData, GetPrevNSecTest,
                         testing::ValuesIn(std::vector<GetPrevNSecParam>{/* begin */
                                                                         {0, 10, 0},
                                                                         {50, 5, 44},
                                                                         {3000, 1000, 2088},
                                                                         {12000, 7329, 6438},
                                                                         {12000, 18000, 954}
                                                                         /* end */}));
