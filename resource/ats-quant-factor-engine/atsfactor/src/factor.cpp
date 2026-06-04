#include "huatai/atsquant/factor/factor_manager.h"

namespace huatai::atsquant::factor {

std::shared_ptr<BaseFactor> BaseFactor::get_factor_(const std::string &name, bool is_nonfactor) {
  if (is_nonfactor) {
    auto fm = fm_.lock();
    auto nonfactor_name = FactorManager::FormatFactorName(fm->get_name(), name);
    return FactorManager::get_factor(nonfactor_name);
  } else {
    return FactorManager::get_factor(name);
  }
}

} // namespace huatai::atsquant::factor