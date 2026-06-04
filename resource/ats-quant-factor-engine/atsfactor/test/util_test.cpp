#include "huatai/atsquant/factor/util.h"

#include <gtest/gtest.h>
#include <map>
#include <set>

using namespace huatai::atsquant::factor;

using TestGraph = std::map<size_t, std::set<size_t>>;
struct TestTopologicalSortParam {
  TestGraph graph;
  std::vector<size_t> expected;
  bool ok;
};
std::vector<TestTopologicalSortParam> test_topological_sort_param = {
    {.graph = {{0, {1}}, {1, {}}, {2, {}}, {3, {}}, {4, {}}, {5, {0, 1}}, {6, {0}}, {7, {}}},
     .expected = {1, 0, 2, 3, 4, 5, 6, 7},
     .ok = true},

    {.graph = {{0, {4}}, {1, {0}}, {2, {1}}, {3, {2}}, {4, {3}}, {5, {0, 1}}, {6, {}}, {7, {}}},
     .expected = {0, 4, 3, 2, 1},
     .ok = false},
};
class TopologicalSortTest : public testing::TestWithParam<TestTopologicalSortParam> {};
TEST_P(TopologicalSortTest, Test) {
  auto [sorted, ok] = topological_sort(GetParam().graph);
  EXPECT_EQ(GetParam().ok, ok);
  EXPECT_EQ(GetParam().expected, sorted);
}
INSTANTIATE_TEST_CASE_P(Util, TopologicalSortTest, testing::ValuesIn(test_topological_sort_param));