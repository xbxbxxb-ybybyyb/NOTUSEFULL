#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/market_data_manager.h"

#include <map>
#include <set>

#ifndef ATSFACTOR_USE_TASKFLOW
#define ATSFACTOR_USE_TASKFLOW 0
#endif

#ifndef ATSFACTOR_USE_OPENMP
#define ATSFACTOR_USE_OPENMP 0
#endif

#if ATSFACTOR_USE_TASKFLOW
#if ATSFACTOR_DEVELOPMENT_MODE
#include <taskflow/taskflow.hpp>
#else
namespace tf {
class Executor;
class Taskflow;
}; // namespace tf
#endif
#endif

namespace huatai::atsquant::factor {
using fmt::format;
using FactorRegistry = std::map<std::string, std::shared_ptr<BaseFactor> (*)()>;
using FactorRuntimeRegistry = std::map<std::string, std::shared_ptr<BaseFactor>>;

struct FactorManagerParam {
  std::string name;
  std::vector<json> factors;
  std::vector<std::string> symbols;
  uint32_t num_threads = 1;
  bool sample_1s = false;
};
inline void to_json(json &nlohmann_json_j, const FactorManagerParam &nlohmann_json_t) {
  nlohmann_json_j["name"] = nlohmann_json_t.name;
  nlohmann_json_j["factors"] = nlohmann_json_t.factors;
  nlohmann_json_j["symbols"] = nlohmann_json_t.symbols;
  nlohmann_json_j["num_threads"] = nlohmann_json_t.num_threads;
  nlohmann_json_j["sample_1s"] = nlohmann_json_t.sample_1s;
}
inline void from_json(const json &nlohmann_json_j, FactorManagerParam &nlohmann_json_t) {
  FactorManagerParam nlohmann_json_default_obj;
  nlohmann_json_t.name = nlohmann_json_j.value("name", nlohmann_json_default_obj.name);
  nlohmann_json_j.at("factors").get_to(nlohmann_json_t.factors);
  nlohmann_json_t.symbols = nlohmann_json_j.value("symbols", nlohmann_json_default_obj.symbols);
  nlohmann_json_t.num_threads = nlohmann_json_j.value("num_threads", nlohmann_json_default_obj.num_threads);
  nlohmann_json_t.sample_1s = nlohmann_json_j.value("sample_1s", nlohmann_json_default_obj.sample_1s);
}

class FACTOR_EXPORT FactorManager : public std::enable_shared_from_this<FactorManager> {
public:
  static Result<std::shared_ptr<FactorManager>> New(const json &param, const MarketDataManagerOption &option = {});

  static const char *DefaultName() { return "default"; }

  static std::string FormatFactorName(const std::string &fm_name, const std::string &factor_type) {
    return format("{}_{}", fm_name, factor_type);
  }

  explicit FactorManager(const json &param = {}, const MarketDataManagerOption &option = {});

  template <typename T>
    requires std::is_base_of_v<BaseFactor, T>
  static Status RegisterFactor() {
    T factor{};
    if (auto [_, inserted] = get_registry().try_emplace(
            factor.get_type(), []() -> std::shared_ptr<BaseFactor> { return std::make_shared<T>(); });
        !inserted) {
      return Status::AlreadyExists("Already exists: ", factor.get_type());
    }
    return Status::OK();
  }

  Status caculate();

  void set_param(const json &param) { param_ = param; }

  void set_option(const MarketDataManagerOption &option) { option_ = option; }

  static std::shared_ptr<BaseFactor> get_factor(const std::string &name);

  std::shared_ptr<BaseFactor> get_factor(size_t runtime_index) const;

  const std::string &get_name() const { return name_; }

  const std::vector<double> &values() const { return values_; }

  std::string to_string() const;

  Status on_quote(const QuoteIndicator &quote);

  std::string dump_taskflow() const;

protected:
  Status init_factors();

  Status init_factor(const FactorParam &param, json &param_json, size_t runtime_index);

  static FactorRegistry &get_registry();

  static FactorRuntimeRegistry &get_runtime_registry();

  std::shared_ptr<MarketDataManager> market_data_manager_;
  MarketDataManagerOption option_;
  std::vector<std::shared_ptr<BaseFactor>> factors_;
  std::vector<double> values_;
  json param_json_;
  FactorManagerParam param_;
  std::string name_ = DefaultName();
#if ATSFACTOR_USE_TASKFLOW
  std::unique_ptr<tf::Executor> executor_;
  std::unique_ptr<tf::Taskflow> taskflow_;
#endif

#ifdef _LATENCY_TEST
  struct FactorLatencyData {
    int64_t caculate_time;
  };
  NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(FactorLatencyData, caculate_time)

  std::vector<FactorLatencyData> factor_latency_data_;
#endif
};

} // namespace huatai::atsquant::factor