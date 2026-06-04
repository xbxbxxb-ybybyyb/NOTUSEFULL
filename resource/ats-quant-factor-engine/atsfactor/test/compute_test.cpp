#include "huatai/atsquant/factor/compute.h"

#include <cfloat>
#include <cmath>
#include <gtest/gtest.h>
#include <vector>

using namespace huatai::atsquant::factor;

struct AggregationParam {
  std::vector<double> v;
  double sum_expect;
  double min_expect;
  double max_expect;
};

class AggregationTest : public testing::TestWithParam<AggregationParam> {};

TEST_P(AggregationTest, Sum) {
  const auto &param = GetParam();
  EXPECT_EQ(param.sum_expect, compute::sum(param.v));
}

TEST_P(AggregationTest, Min) {
  const auto &param = GetParam();
  EXPECT_EQ(param.min_expect, compute::min(param.v));
}

TEST_P(AggregationTest, Max) {
  const auto &param = GetParam();
  EXPECT_EQ(param.max_expect, compute::max(param.v));
}

INSTANTIATE_TEST_CASE_P(compute, AggregationTest,
                        testing::ValuesIn(std::vector<AggregationParam>({/* begin */
                                                                         {{1, 2, 3}, 6, 1, 3},
                                                                         {{1, 2, 3, 4, 5, 6, 7, 8}, 36, 1, 8},
                                                                         {{1, 2, 3, 4, 5, 6, 7, 8, 9}, 45, 1, 9},
                                                                         {{}, 0, DBL_MAX, -DBL_MAX}
                                                                         /* end */})));
struct StdParam {
  std::vector<double> v;
  double expect;
};

class StdTest : public testing::TestWithParam<StdParam> {};
TEST_P(StdTest, Test) {
  const auto &param = GetParam();
  EXPECT_EQ(param.expect, compute::std(param.v));
}

INSTANTIATE_TEST_CASE_P(
    compute, StdTest,
    testing::ValuesIn(std::vector<StdParam>({/* begin */
                                             {{999}, 0},
                                             {{3, 3, 3}, 0},
                                             {{0, 4}, 2.8284271247461903},
                                             {{25, 100, 25, 100, 25, 100, 100, 100, 25, 25}, 39.528470752104745},
                                             {{1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1}, 2.537947294682897}
                                             /* end */})));

struct ScalarParam {
  std::vector<double> v;
  double scalar;
  std::vector<double> add_expect;
  std::vector<double> sub_expect;
  std::vector<double> mul_expect;
  std::vector<double> div_expect;
};
class ScalarTest : public testing::TestWithParam<ScalarParam> {};
TEST_P(ScalarTest, Add) {
  const auto &param = GetParam();
  auto v = param.v;
  compute::add(v, param.scalar);
  EXPECT_EQ(param.add_expect, v);
}
TEST_P(ScalarTest, Sub) {
  const auto &param = GetParam();
  auto v = param.v;
  compute::sub(v, param.scalar);
  EXPECT_EQ(param.sub_expect, v);
}
TEST_P(ScalarTest, Mul) {
  const auto &param = GetParam();
  auto v = param.v;
  compute::mul(v, param.scalar);
  EXPECT_EQ(param.mul_expect, v);
}
TEST_P(ScalarTest, Div) {
  const auto &param = GetParam();
  auto v = param.v;
  compute::div(v, param.scalar);
  EXPECT_EQ(param.div_expect, v);
}
INSTANTIATE_TEST_CASE_P(compute, ScalarTest,
                        testing::ValuesIn(std::vector<ScalarParam>(
                            {/* begin */
                             {{}, 100, {}, {}, {}, {}},
                             {{1, 2}, 3, {4, 5}, {-2, -1}, {3, 6}, {1.0 / 3, 2.0 / 3}},
                             {{-5, 0, 1, 2, 3, 4, 5, 6, 7, 8},
                              5,
                              {0, 5, 6, 7, 8, 9, 10, 11, 12, 13},
                              {-10, -5, -4, -3, -2, -1, 0, 1, 2, 3},
                              {-25, 0, 5, 10, 15, 20, 25, 30, 35, 40},
                              {-1, 0, 1.0 / 5, 2.0 / 5, 3.0 / 5, 4.0 / 5, 1, 6.0 / 5, 7.0 / 5, 8.0 / 5}}
                             /* end */})));
struct VecParam {
  std::vector<double> va;
  std::vector<double> vb;
  std::vector<double> add_expect;
  std::vector<double> sub_expect;
  std::vector<double> mul_expect;
  std::vector<double> div_expect;
};
class VecTest : public testing::TestWithParam<VecParam> {};
TEST_P(VecTest, Add) {
  const auto &param = GetParam();
  auto va = param.va;
  compute::add(va, param.vb);
  EXPECT_EQ(param.add_expect, va);
}
TEST_P(VecTest, Sub) {
  const auto &param = GetParam();
  auto va = param.va;
  compute::sub(va, param.vb);
  EXPECT_EQ(param.sub_expect, va);
}
TEST_P(VecTest, Mul) {
  const auto &param = GetParam();
  auto va = param.va;
  compute::mul(va, param.vb);
  EXPECT_EQ(param.mul_expect, va);
}
TEST_P(VecTest, Div) {
  const auto &param = GetParam();
  auto va = param.va;
  compute::div(va, param.vb);
  EXPECT_EQ(param.div_expect, va);
}
INSTANTIATE_TEST_CASE_P(
    compute, VecTest,
    testing::ValuesIn(std::vector<VecParam>({/* begin */
                                             {{}, {}, {}, {}, {}, {}},
                                             {{1, 2}, {3, 4}, {4, 6}, {-2, -2}, {3, 8}, {1.0 / 3, 2.0 / 4}},
                                             {{-3, -2, -1, 0, 1, 2, 3},
                                              {-2, -1, 0, 1, 2, 3, 4},
                                              {-5, -3, -1, 1, 3, 5, 7},
                                              {-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0},
                                              {6.0, 2.0, -0.0, 0.0, 2.0, 6.0, 12.0},
                                              {1.5, 2.0, -INFINITY, 0.0, 0.5, 2.0 / 3, 0.75}}
                                             /* end */})));

struct DiffParam {
  std::vector<double> v;
  std::vector<double> expect;
};
class DiffTest : public testing::TestWithParam<DiffParam> {};
TEST_P(DiffTest, Test) {
  const auto &param = GetParam();
  EXPECT_EQ(param.expect, compute::diff(param.v));
}
INSTANTIATE_TEST_CASE_P(
    compute, DiffTest,
    testing::ValuesIn(std::vector<DiffParam>({/* begin */
                                              {{}, {}},
                                              {{1}, {}},
                                              {{3, 9}, {6}},
                                              {{-4, 1, -2, -10, 3,  4,  5,  -9, -3, -4, 7, -1,  2,  6, 6,
                                                -2, 8, -5, -6,  -2, -9, -3, -7, -9, 10, 7, -10, -9, 8, -7},
                                               {5,  -3,  -8, 13, 1,  1, -14, 6,  -1, 11, -8,  3, 4,  0,  -8,
                                                10, -13, -1, 4,  -7, 6, -4,  -2, 19, -3, -17, 1, 17, -15}}
                                              /* end */})));

struct FilterParam {
  std::vector<double> v;
  std::function<bool(size_t, const double &)> filter_fn;
  std::vector<double> expect;
};

class FilterTest : public testing::TestWithParam<FilterParam> {};

TEST_P(FilterTest, Test) {
  const auto &param = GetParam();
  EXPECT_EQ(param.expect, compute::filter(param.v, param.filter_fn));
}

INSTANTIATE_TEST_CASE_P(
    compute, FilterTest,
    testing::ValuesIn(std::vector<FilterParam>(
        {/* begin */
         {{1, 2, 3, 4, 5, 6, 7, 8, 9}, [](size_t i, const double &v) { return i % 2 == 1; }, {2, 4, 6, 8}},
         {{1, 2, 3, 4, 5, 6, 7, 8, 9}, [](size_t i, const double &v) { return i % 2 == 0; }, {1, 3, 5, 7, 9}},
         /* end */})));