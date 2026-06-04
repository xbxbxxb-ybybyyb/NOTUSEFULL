# AutoMiningHFF

-  ## **1.高频因子自动挖掘数据部分 data-automining**

    高频因子自动挖掘项目中的数据准备部分，不封装到sdk中

   - ### 1.1 生成增强trade数据 gen enhanced trade
    
             * 包括增强Trade数据的历史补数和每日更新脚本
        
             * 支持新增增强Trade数据字段
             
   - ### 1.2 已发布因子的更新 online factor update
             * online_factor_calc_daily
             
             * online_factor_calc_his

- ## **2. 高频因子自动挖掘框架部分 - AutoMiningFrame**
    包括因子挖掘框架，因子计算框架，因子存取框架，因子评价模块等
    
     -  ### 2.1 Dolphin相关配置文件+modules DolphinDBServer
          
            * server 启动dolphindb服务的命令
            
            * modules： dolphindb模块文件，包括计算模块，存取模块，评价模块等

     - ### 2.2 因子计算+存取框架 DataCalculation

            * entry: 入口文件
            
            * factors: 用于测试的因子文件
    
            * utils : 公共文件        
    
            * config： 相关配置文件

     - ###2.3 因子挖掘模块 FactorAutoMining

         *

     - ### 2.4 因子评价模块 FactorBacktest
      
              * entry: 入口文件
              
              * utils：公共方法
              
              * configs： 相关配置文件
