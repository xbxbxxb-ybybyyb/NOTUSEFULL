#include "huatai/atsquant/factor/factor_manager.h"
#include "huatai/atsquant/factor/all_factors.h"

#include <fmt/format.h>

#if ATSFACTOR_USE_OPENMP
#include <omp.h>
#elif ATSFACTOR_USE_TASKFLOW
#include <taskflow/taskflow.hpp>
#else
static_assert("missing parallel framework");
#endif

namespace huatai::atsquant::factor {

FactorManager::FactorManager(const json &param, const MarketDataManagerOption &option)
    : param_json_(param), option_(option) {
  market_data_manager_ = MarketDataManager::Instance(option);

  param_json_.get_to(param_);

  if (!param_.name.empty()) {
    name_ = param_.name;
  }
}

Result<std::shared_ptr<FactorManager>> FactorManager::New(const json &param, const MarketDataManagerOption &option) {
  if (get_registry().empty()) {
    ARROW_RETURN_NOT_OK(register_all_types());
  }

  try {
    auto fm = std::make_shared<FactorManager>(param, option);
    ARROW_RETURN_NOT_OK(fm->init_factors());
    return fm;
  } catch (const std::exception &e) {
    return Status::UnknownError("Failed to create FactorManager, ", e.what());
  }
}

Status FactorManager::init_factors() {
#if ATSFACTOR_USE_OPENMP
  omp_set_num_threads(param_.num_threads);
#elif ATSFACTOR_USE_TASKFLOW
  executor_ = std::make_unique<tf::Executor>(param_.num_threads);
  taskflow_ = std::make_unique<tf::Taskflow>();
#endif

  factors_.resize(param_.factors.size());
  values_.resize(param_.factors.size());
#ifdef _LATENCY_TEST
  factor_latency_data_.resize(param_.factors.size());
#endif

  std::vector<FactorParam> factors;
  try {
    for (const auto &j : param_.factors) {
      factors.emplace_back(j.get<FactorParam>());
    }
  } catch (const std::exception &e) {
    return Status::UnknownError("Bad param: ", param_json_, ", exception: ", e.what());
  }

  // 初始化行情管理器:
  // 1. 在因子管理器中指定了标的列表，初始化这些行情管理器
  for (const auto &symbol : param_.symbols) {
    market_data_manager_->add_symbol(symbol);
  }

  // 2. 在因子中指定了标的，初始化这些行情管理器
  for (const auto &param : factors) {
    for (const auto &symbol : param.symbols) {
      market_data_manager_->add_symbol(symbol);
    }
  }

  // 3. 没有指定任何标的，只初始化一个行情管理器
  if (market_data_manager_->size() == 0) {
    market_data_manager_->add_symbol({});
  }

  // 解析因子名称与运行时索引的关系，用于拓扑排序
  std::map<std::string, size_t> name_to_index;
  for (size_t i = 0; i < factors.size(); i++) {
    auto &factor = factors[i];
    if (factor.name.empty()) {
      factor.name = FormatFactorName(get_name(), factor.type);
    }

    name_to_index[factor.name] = i;
  }

  // 解析因子执行拓扑，根据拓扑顺序初始化因子
  std::map<size_t, std::set<size_t>> dependencies;
  for (size_t i = 0; i < factors.size(); i++) {
    const auto &factor = factors[i];
    auto [it, _] = dependencies.try_emplace(i);
    if (factor.dependencies.empty()) {
      continue;
    }

    if constexpr (!ATSFACTOR_USE_TASKFLOW) {
      return Status::UnknownError("Taskflow is disabled, unable to solve dependencies: ", json(factor).dump());
    }

    for (auto d : factor.dependencies) {
      size_t dependency_index;
      auto it2 = name_to_index.find(d);
      if (it2 == name_to_index.end()) {
        // assume it is nonfactor
        d = FormatFactorName(get_name(), d);
        auto it3 = name_to_index.find(d);
        if (it3 == name_to_index.end()) {
          return Status::UnknownError(
              format("Invalid factor dependency in type \"{}\", name \"{}\": {}", factor.type, factor.name, d));
        }
        dependency_index = it3->second;
      } else {
        dependency_index = it2->second;
      }

      it->second.insert(dependency_index);
    }
  }

  auto [sorted, ok] = topological_sort(dependencies);
  if (!ok) {
    std::vector<std::string> circle;
    for (auto i : sorted) {
      circle.emplace_back(factors[i].name);
    }
    return Status::UnknownError("Circular dependency: ", json(circle).dump());
  }

#if ATSFACTOR_USE_TASKFLOW
  std::vector<tf::Task> tasks(factors.size());
#endif

  for (auto runtime_index : sorted) {
    ARROW_RETURN_NOT_OK(init_factor(factors[runtime_index], param_.factors[runtime_index], runtime_index));

#if ATSFACTOR_USE_TASKFLOW
    auto f = factors_[runtime_index];
    auto task = taskflow_->emplace([this, factor = std::move(f)]() {
      if (param_.sample_1s && !factor->nonfactor_ &&
          factor->get_market_data().get_prev_n_quote(1).item<QuoteSchema::Index::SAMPLE_1S_FLAG>() == 0) {
        return Status::OK();
      }

#ifdef _LATENCY_TEST
      auto now = now_in_nano();
#endif
      auto s = factor->caculate();
#ifdef _LATENCY_TEST
      factor_latency_data_[factor->get_runtime_index()].caculate_time += now_in_nano() - now;
#endif

      return s;
    });

    task.name(factors[runtime_index].name);
    tasks[runtime_index] = task;
    for (auto j : dependencies[runtime_index]) {
      task.succeed(tasks[j]);
    }
#endif
  }

  return Status::OK();
}

Status FactorManager::init_factor(const FactorParam &param, json &param_json, size_t runtime_index) {
  auto it = get_registry().find(param.type);
  if (it == get_registry().end()) {
    return Status::KeyError("Factor not registered: ", param.type);
  }

  auto factor = it->second();

  factor->name_ = param.name;
  if (auto [it, inserted] = get_runtime_registry().try_emplace(factor->get_name(), factor); !inserted) {
    return Status::AlreadyExists("Factor name already in use: ", factor->get_name());
  }

  factors_[runtime_index] = factor;
  factor->runtime_index_ = runtime_index;
  factor->value_ = &values_[factor->get_runtime_index()];
  factor->mdm_ = market_data_manager_;
  factor->fm_ = weak_from_this();
  factor->nonfactor_ = is_nonfactor_runtime(factor->get_type());

  // 设置因子行情默认标的
  if (!param_.symbols.empty()) {
    // FactorManager参数指定了标的列表
    // 第一个标的为因子默认标的
    factor->default_mdm_ = market_data_manager_->get_manager(param_.symbols[0]);

    // symbols透传至因子参数
    if (!param_json.contains("symbols")) {
      param_json["symbols"] = param_.symbols;
    }
  } else if (market_data_manager_->size() == 1) {
    // 参数未指定默认标的，全局行情管理器只有一个标的
    factor->default_mdm_ = market_data_manager_->default_manager();
  }

  ARROW_RETURN_NOT_OK(factor->init(param_json));

  return Status::OK();
}

FactorRegistry &FactorManager::get_registry() {
  static FactorRegistry registry_;
  return registry_;
}

FactorRuntimeRegistry &FactorManager::get_runtime_registry() {
  static FactorRuntimeRegistry runtime_registry_;
  return runtime_registry_;
}

Status FactorManager::caculate() {
  Status st{};

#if ATSFACTOR_USE_OPENMP
#pragma omp parallel shared(st)
  {
#pragma omp for
    for (auto it = factors_.begin(); it != factors_.end(); it++) {
      auto &factor = *it;
      if (param_.sample_1s && !factor->nonfactor_ &&
          factor->get_market_data().get_prev_n_quote(1).item<QuoteSchema::Index::SAMPLE_1S_FLAG>() == 0) {
        continue;
      }

#ifdef _LATENCY_TEST
      auto now = now_in_nano();
#endif
      auto s = factor->caculate();
#ifdef _LATENCY_TEST
      factor_latency_data_[factor->get_runtime_index()].caculate_time += now_in_nano() - now;
#endif

      if (!s.ok()) {
#pragma omp critical
        { st &= s; }
#pragma omp cancel for
      }
    }
  }
#elif ATSFACTOR_USE_TASKFLOW
  // todo: reduce Status?
  executor_->run(*taskflow_).wait();
#endif

  return st;
}

std::shared_ptr<BaseFactor> FactorManager::get_factor(const std::string &name) {
  auto it = get_runtime_registry().find(name);
  if (it == get_runtime_registry().end()) {
    return nullptr;
  }
  return it->second;
}

std::shared_ptr<BaseFactor> FactorManager::get_factor(size_t runtime_index) const {
  return runtime_index >= factors_.size() ? nullptr : factors_[runtime_index];
}

std::string FactorManager::to_string() const {
  json j;
  std::vector<std::string> v;
  for (const auto &[type, _] : get_registry()) {
    v.emplace_back(type);
  }
  j["registered"] = v;

  for (const auto &factor : factors_) {
#ifdef _LATENCY_TEST
    j["runtime"][factor->get_name()] =
        format("{:.9f}", (double)factor_latency_data_[factor->get_runtime_index()].caculate_time / 1e9);
#else
    j["runtime"].emplace_back(factor->get_name());
#endif
  }

  return j.dump(2);
}

Status FactorManager::on_quote(const QuoteIndicator &quote) { return market_data_manager_->on_quote(quote); }

std::string FactorManager::dump_taskflow() const {
#if ATSFACTOR_USE_TASKFLOW
  return taskflow_->dump();
#else
  return "Taskflow is disabled";
#endif
}

} // namespace huatai::atsquant::factor
