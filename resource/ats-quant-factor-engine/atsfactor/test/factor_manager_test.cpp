#include "huatai/atsquant/factor/factor_manager.h"

#include <gtest/gtest.h>

using namespace huatai::atsquant::factor;

class FactorManagerTest : public testing::Test {
protected:
  void SetUp() override {}

  std::shared_ptr<FactorManager> fm_;
  Status st;
  Result<std::shared_ptr<FactorManager>> re;
};

class TestFactor : public Factor<> {
public:
  TestFactor() { type_ = __func__; }
};

TEST_F(FactorManagerTest, TestRegister) {
  fm_ =
      FactorManager::New(FactorManagerParam{},
                         MarketDataManagerOption{.type = MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE})
          .ValueUnsafe();
  auto st = FactorManager::RegisterFactor<TestFactor>();
  ASSERT_TRUE(st.ok()) << st.ToString();
  st = FactorManager::RegisterFactor<TestFactor>();
  ASSERT_FALSE(st.ok());
}

TEST_F(FactorManagerTest, InitFactorNoList) {
  re = FactorManager::New(R"({"factors": {"not": "a vector"}})"_json);
  st = re.status();
  ASSERT_FALSE(st.ok()) << st.ToString();
  EXPECT_EQ(st.code(), arrow::StatusCode::UnknownError);
}

TEST_F(FactorManagerTest, InitFactorNoType) {
  re = FactorManager::New(R"({"factors": [{"no": "type"}]})"_json);
  st = re.status();
  ASSERT_FALSE(st.ok()) << st.ToString();
  st = re.status();
  ASSERT_FALSE(st.ok()) << st.ToString();
  EXPECT_EQ(st.code(), arrow::StatusCode::UnknownError);
}

TEST_F(FactorManagerTest, InitFactorInvalidType) {
  re = FactorManager::New(R"({"factors": [{"type": "invalid"}]})"_json);
  st = re.status();
  ASSERT_FALSE(st.ok()) << st.ToString();
  st = re.status();
  ASSERT_FALSE(st.ok()) << st.ToString();
  EXPECT_EQ(st.code(), arrow::StatusCode::KeyError);
}

TEST_F(FactorManagerTest, InitFactorNameAlreadyInUse) {
  st = FactorManager::RegisterFactor<TestFactor>();
  re = FactorManager::New(R"({"factors": [{"type": "TestFactor"}, {"type": "TestFactor"}]})"_json);
  ASSERT_FALSE(re.ok());
  st = re.status();
  ASSERT_FALSE(st.ok()) << st.ToString();
  EXPECT_EQ(st.code(), arrow::StatusCode::AlreadyExists);
}

TEST_F(FactorManagerTest, InitFactorOK) {
  st = FactorManager::RegisterFactor<TestFactor>();
  re = FactorManager::New(
      R"({
        "name": "foo", 
        "factors": [
          {"type": "TestFactor"}, 
          {"type": "TestFactor", "name": "bar"}
        ]
      })"_json);
  ASSERT_TRUE(re.ok());
  fm_ = re.ValueUnsafe();
  EXPECT_EQ(fm_->get_name(), "foo");

  auto factor = FactorManager::get_factor("bar");
  ASSERT_NE(factor, nullptr);
  EXPECT_EQ(factor->get_name(), "bar");

  factor = FactorManager::get_factor("foo_TestFactor");
  ASSERT_NE(factor, nullptr);
  EXPECT_EQ(factor->get_name(), "foo_TestFactor");

  ASSERT_EQ(FactorManager::get_factor("foo_bar"), nullptr);
}