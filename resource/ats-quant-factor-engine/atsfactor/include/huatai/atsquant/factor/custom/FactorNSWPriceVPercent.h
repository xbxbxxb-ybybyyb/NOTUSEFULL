#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

#include <deque>

namespace huatai::atsquant::factor {

class FactorNSWPriceVPercent : public Factor<> {
  static const int LAG = 20;
  SlidingWindow<double> ret_list{LAG};
  SlidingWindow<double> vol_list{LAG};
  SlidingWindow<double> mvol_list{LAG};

  template <typename V> static double percent_bigger_than_new_value(const V &X) {
    if (X.size() == 0) {
      return 0;
    }

    auto new_value = X.back();
    size_t num_bigger = 0;
    for (const auto &i : X) {
      num_bigger += i > new_value;
    }
    return (double)num_bigger / X.size();
  }


public:
  FactorNSWPriceVPercent() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_quote(2);
    if(table.len()<2){
      ret_list.push(-1000);
      return Status::OK();
    }
    auto now = table[1];
    auto last = table[0];
    auto lastpx_cur = now.item<QuoteSchema::Index::LAST_PX>();
    auto lastpx_pre = last.item<QuoteSchema::Index::LAST_PX>();
    auto ret = (lastpx_cur - lastpx_pre) / lastpx_cur;
    ret_list.push(ret);
    auto ttl_volumne_cur = now.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto ttl_volumne_last = last.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto vol = ttl_volumne_cur - ttl_volumne_last;
    vol_list.push(vol);
    auto mvol = compute::sum(vol_list);
    mvol_list.push(mvol);
    auto vol_percent = percent_bigger_than_new_value(mvol_list);
    auto ret_percent = percent_bigger_than_new_value(ret_list);

    value() = ret_percent*vol_percent;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor