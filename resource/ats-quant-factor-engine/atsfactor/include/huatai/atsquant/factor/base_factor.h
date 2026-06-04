#pragma once

#include <memory>
#include <nlohmann/json.hpp>
#include <span>

#include "huatai/atsquant/factor/market_data_manager.h"
#include "huatai/atsquant/factor/type_traits.h"

namespace huatai::atsquant::factor {
using json = nlohmann::json;

class FactorManager;

class FACTOR_EXPORT BaseFactor {
public:
  using __value_type = double;

  BaseFactor() = default;

  virtual ~BaseFactor() {}

  virtual Status init(const json &param_json) {
    param_json_ = param_json;
    return Status::OK();
  }

  virtual void on_init() {}

  virtual Status caculate() { return Status::OK(); }

  std::string get_type() const { return type_; }

  std::string get_name() const { return name_; }

  int64_t get_runtime_index() const { return runtime_index_; }

  SingleMarketDataManager &get_market_data() { return *default_mdm_; }

  SingleMarketDataManager &get_market_data(const std::string &symbol) { return *mdm_->get_manager(symbol); }

  __value_type &value() { return *value_; };

  template <typename FactorType>
    requires is_nonfactor_v<FactorType>
  std::shared_ptr<FactorType> get_factor() {
    return std::static_pointer_cast<FactorType>(get_factor_(is_nonfactor<FactorType>::type, true));
  }

  template <typename FactorType = BaseFactor> std::shared_ptr<FactorType> get_factor(const std::string &name) {
    return std::static_pointer_cast<FactorType>(get_factor_(name));
  }

  void set_value(__value_type v) {
    value_history_.emplace_back(v);
    value() = v;
  }

  std::span<const __value_type> value_history() const noexcept { return value_history_; }

protected:
  std::shared_ptr<BaseFactor> get_factor_(const std::string &name, bool is_nonfactor = false);

  std::shared_ptr<SingleMarketDataManager> default_mdm_;
  std::shared_ptr<MarketDataManager> mdm_;
  std::weak_ptr<FactorManager> fm_;
  std::string type_;
  std::string name_;
  json param_json_;
  int64_t runtime_index_ = -1;
  __value_type *value_;
  std::vector<__value_type> value_history_;
  bool nonfactor_;

  friend class FactorManager;
};

struct FactorParam {
  std::string type;
  std::string name;
  std::vector<std::string> symbols;
  std::vector<std::string> dependencies;
};
inline void to_json(json &nlohmann_json_j, const FactorParam &nlohmann_json_t) {
  nlohmann_json_j["type"] = nlohmann_json_t.type;
  nlohmann_json_j["name"] = nlohmann_json_t.name;
  nlohmann_json_j["symbols"] = nlohmann_json_t.symbols;
  nlohmann_json_j["dependencies"] = nlohmann_json_t.dependencies;
}
inline void from_json(const json &nlohmann_json_j, FactorParam &nlohmann_json_t) {
  FactorParam nlohmann_json_default_obj;
  nlohmann_json_j.at("type").get_to(nlohmann_json_t.type);
  nlohmann_json_t.name = nlohmann_json_j.value("name", nlohmann_json_default_obj.name);
  nlohmann_json_t.symbols = nlohmann_json_j.value("symbols", nlohmann_json_default_obj.symbols);
  nlohmann_json_t.dependencies = nlohmann_json_j.value("dependencies", nlohmann_json_default_obj.dependencies);
}

template <typename ParamType = FactorParam> class Factor : public BaseFactor {
public:
  Status init(const json &param_json) override {
    ARROW_RETURN_NOT_OK(BaseFactor::init(param_json));
    try {
      param_json.get_to(param_);
    } catch (const std::exception &e) {
      return Status::UnknownError("Parse param of \"", type_, "\" failed: ", e.what(), ", param: ", param_json.dump());
    }

    on_init();
    return Status::OK();
  }

  ParamType &param() { return param_; };

protected:
  ParamType param_;
};

} // namespace huatai::atsquant::factor