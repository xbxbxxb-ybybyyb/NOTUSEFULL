// 如何创建一个自定义因子：
//  1. 定义自定义参数，并定义序列化方法
//  2. 定义因子类，关联自定义参数
//  3. 为因子命名
//  4. 实现因子计算逻辑

#pragma once

#include <huatai/atsquant/factor.h>
#include <nlohmann/json.hpp>

namespace huatai::atsquant::factor {

// 每个因子可以自定义参数，类型继承自FactorParam
// 为了能正确的从nlohmann::json结构中解析，需要使用宏对自定义参数序列化，可选择的宏有：
//  - NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE: 如果参数反序列化缺少key，因子初始化也会失败
//  - NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT：如果反序列化缺少key、缺少的key会使用默认值
//
// 因子自定义参数会在因子初始化(init)时填入，之后通过 param() 或者 param_ 来获取
// 参数的原始json也可以通过 param_json_ 来获取
struct MyFactorParam : public FactorParam {
  int int_param = 1;
};
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT(MyFactorParam, int_param)

// 自定义因子类，此类型必须继承Factor<>，模板参数为自定义因子类型
// 如果没有自定义参数类型，可以直接继承Factor<>
class MyFactor : public Factor<MyFactorParam> {
public:
  // 因子初始化有两个阶段：
  //    1. 构造函数：在因子管理器(FactorManager) 创建时，同时会创建所有内置因子。不应该失败
  //    2. Status init(const json &param_json) override; 在因子管理器(FactorManager) 调用
  //    init_factors()时，调用此方法。允许失败
  //
  // 必须定义因子的构造函数，type_设置为因子类名
  MyFactor() { type_ = __func__; }

  // init方法可选，如果因子没有很多初始化逻辑，可以不定义此方法
  // 如果需要特定的初始化，必须先调用父类的init
  Status init(const json &param_json) override {
    ARROW_RETURN_NOT_OK(Factor::init(param_json));

    // 有其他初始化逻辑
    // ...
    if (false) {
      // 失败
      return Status::UnknownError("Init failed: ", "discription");
    }

    // 成功
    return Status::OK();
  }

  // 因子计算逻辑，必须实现
  // 在因子管理器(FactorManager) 调用 caculate() 时，会调用此方法
  Status caculate() override {
    // 因子计算输出为double类型。由于运行时因子数量并不确定，因此输出的地址只能在运行时确定
    // 因子类有成员变量 value_，它是一个double * ，在init被调用前，value_ 是空指针，在init后，value_指向输出地址
    // 由于因子并不保存历史输出，如果需要历史输出，可以在caculate中取出上一次的输出值：
    auto prev = value();

    // 等价于：
    prev = *value_;

    // 每次计算可以选择将输出重置为0
    value() = 0;

    // 需要获取因子参数，它的类型是关联类型MyParam：
    auto v = param().int_param;

    // 等价于：
    v = param_.int_param;

    // 因子计算可以返回错误。是否导致停止计算，由因子管理器决定
    if (false) {
      // 失败
      // arrow::Status 的异常处理逻辑需要申请堆内存存储错误信息，而正常逻辑仅返回一个8字节指针，
      // 因此异常处理比正常慢很多，不建议频繁触发异常，却不停止计算
      return Status::UnknownError("Caculate failed: ", "discription");
    }

    // 计算结果存储在value_指针中
    value() = v * 100;

    // 成功
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor