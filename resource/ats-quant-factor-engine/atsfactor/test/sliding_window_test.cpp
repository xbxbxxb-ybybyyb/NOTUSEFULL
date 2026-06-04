#include "huatai/atsquant/factor/sliding_window.h"

#include <gtest/gtest.h>

using namespace huatai::atsquant::factor;

struct SlidingWindowParam {
  size_t window_size;
  std::vector<int> sequence;
  std::vector<int> expected_front;
};
class SlidingWindowTest : public testing::TestWithParam<SlidingWindowParam> {};
TEST_P(SlidingWindowTest, Test) {
  SlidingWindow<int> sw{GetParam().window_size};
  ASSERT_EQ(GetParam().sequence.size(), GetParam().expected_front.size());

  for (size_t i = 0; i < GetParam().sequence.size(); i++) {
    sw.push(GetParam().sequence[i]);
    ASSERT_EQ(sw.front(), GetParam().expected_front[i]);
  }
}
std::vector<SlidingWindowParam> sliding_window_param = {
    {.window_size = 1, .sequence = {1, 2, 3}, .expected_front = {1, 2, 3}},
    {.window_size = 3, .sequence = {1, 2, 3, 4, 5, 6, 7, 8, 9}, .expected_front = {1, 1, 1, 2, 3, 4, 5, 6, 7}},
};
INSTANTIATE_TEST_CASE_P(SlidingWindow, SlidingWindowTest, testing::ValuesIn(sliding_window_param));

struct TimeSlidingWindowParam {
  int64_t seconds;
  std::vector<int64_t> sequence;
  std::vector<int> expected_front;
};
class TimeSlidingWindowTest : public testing::TestWithParam<TimeSlidingWindowParam> {};
TEST_P(TimeSlidingWindowTest, Test) {
  TimeSlidingWindow<int> sw{GetParam().seconds};
  ASSERT_EQ(GetParam().sequence.size(), GetParam().expected_front.size());

  for (size_t i = 0; i < GetParam().sequence.size(); i++) {
    sw.push(GetParam().sequence[i], GetParam().sequence[i]);
    ASSERT_EQ(sw.front(), GetParam().expected_front[i]) << "i = " << i;
  }
}
std::vector<TimeSlidingWindowParam> time_sliding_window_param = {
    TimeSlidingWindowParam{
        .seconds = 1, .sequence = {0, 500, 1000, 1500, 2000}, .expected_front = {0, 0, 500, 1000, 1500}},

    TimeSlidingWindowParam{.seconds = 1,
                           .sequence = {0, 1, 2, 1000, 1000, 1002, 2000, 2001, 2002, 2003},
                           .expected_front = {0, 0, 0, 1, 1, 1000, 1002, 1002, 2000, 2000}},

    TimeSlidingWindowParam{.seconds = 2,
                           .sequence = {0, 1, 2, 1000, 1000, 1002, 2000, 2001, 2002, 2003},
                           .expected_front = {0, 0, 0, 0, 0, 0, 1, 2, 1000, 1000}},
};
INSTANTIATE_TEST_CASE_P(SlidingWindow, TimeSlidingWindowTest, testing::ValuesIn(time_sliding_window_param));
