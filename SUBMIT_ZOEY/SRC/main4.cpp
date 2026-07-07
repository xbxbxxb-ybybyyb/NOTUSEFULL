#include<string>
#include<iostream>
#include<sys/mman.h>
#include<sys/types.h>
#include<fcntl.h>
#include<string.h>
#include<stdio.h>
#include<unistd.h>
#include<assert.h>
#include <bits/stdc++.h>
#include "SRC/framework/graphnode.h"
#include "SRC/framework/niobase.h"
#include "SRC/framework/registerdata.h"
#include "SRC/framework/register.h"
#include "SRC/framework/util.h"

using namespace std;

int64_t TS()//print current time stamp
{
  std::chrono::system_clock::time_point currentTime = std::chrono::system_clock::now();
  std::chrono::microseconds epochTime = std::chrono::duration_cast<std::chrono::microseconds>(currentTime.time_since_epoch());
  return epochTime.count();
}




namespace GLOBAL
{
  double global_price = 0;
  double global_qty = 0;
  std::string global_body;
  std::string global_headline;
  int64_t global_timestamp = 0;

  int64_t macro_seconds_used_by_framework = 0;
  int64_t macro_seconds_used_by_no_framework = 0;

}

//////////////////////////////////////////////
//

/* @brief TimeLoc use int64_t to keep the timestamp
 */

class TimeLoc:public GraphNodeBase
{
  NIO_MATRIX<int64_t> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    int64_t& output = *(sig.GetBasePtr());
    output = GLOBAL::global_timestamp;
  }
};

REGISTER(TimeLoc);


/* @brief VolumeLoc use double to keep the trading volume
 */
class VolumeLoc:public GraphNodeBase
{
  NIO_MATRIX<double> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    double& output = *(sig.GetBasePtr());
    output = GLOBAL::global_qty;
  }
};

REGISTER(VolumeLoc);


/* @brief PriceLoc use double to keep the trade price
 */

class PriceLoc:public GraphNodeBase
{
  NIO_MATRIX<double> sig;//merge many VD to VVD
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    double& output = *(sig.GetBasePtr());
    output = GLOBAL::global_price;
  }

};

REGISTER(PriceLoc);

/* @brief StatDiff keep the price diff feature
 * @param depend on price node
 * @return 
 */

class StatDiff:public GraphNodeBase
{
  NIO_MATRIX<double> sig;//merge many VD to VVD

  deque<double> dq;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<double> &nio_ft = dr->GetData<NIO_MATRIX, double>("price");
    const double& prc = *(nio_ft.GetBasePtr());

    dq.push_back(prc);
    while (dq.size() > 2) dq.pop_front();
    
    double& output = *(sig.GetBasePtr());
    if (dq.size() <= 1) output = 0;//define price diff = 0 when only one sample
    else output = dq.back() - dq[0];//dq[1] - dq[0]
  }
};

REGISTER(StatDiff);


/* @brief StatMean keep the price mean
 * @param depend on price node
 * @return  mean price
 */

class StatMean:public GraphNodeBase
{
  NIO_MATRIX<double> sig;
  double cum_sum;
  double cum_cnt;
public:
  void Initialize(const string &para)
  {
    cum_sum = 0;
    cum_cnt = 0;
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<double> &nio_ft = dr->GetData<NIO_MATRIX, double>("price");
    const double& prc = *(nio_ft.GetBasePtr());
    

    //each time we get a new price observation, we need to update cummulative sum and cnt
    cum_sum += prc;
    cum_cnt += 1.0;
    
    double& output = *(sig.GetBasePtr());

    //mean price always = cummulative sum / cummulative cnt
    output = (cum_cnt > 0)? cum_sum / cum_cnt:0.0;
    //std::cout<<"FRAMEWORK(" + tag + "):"<<output<<std::endl;
  }
};

REGISTER(StatMean);


class GroupByMeanStd:public GraphNodeBase
{
  NIO_MATRIX<double> sig;
  unordered_map<int, pair<double, double>> gbsum_cnt;
  vector<double> cache;
public:
  void Initialize(const string &para)
  {
    cache = vector<double>(3, 0);
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    int64_t start_timestamp = TS();
    const NIO_MATRIX<double> &nio_ft0 = dr->GetData<NIO_MATRIX, double>("price");
    const NIO_MATRIX<double> &nio_ft1 = dr->GetData<NIO_MATRIX, double>("volume");
    const double& prc = *(nio_ft0.GetBasePtr());
    const double& qty = *(nio_ft1.GetBasePtr());

    int nid = static_cast<int>(prc);
    double v = qty;
    unordered_map<int, pair<double, double>>::iterator zz = gbsum_cnt.find(nid);

    double up = cache[1];//need to adjust it
    double up2 = cache[2];//need to adjust it

    if (zz != gbsum_cnt.end()) {
      double olds = (*zz).second.first;//gbsum[nid];
      double oldc = (*zz).second.second;//gbcnt[nid];
      (*zz).second.first = olds + v;
      (*zz).second.second = oldc + 1;
      double nv = (olds + v) / (oldc + 1);
      double ov = olds / oldc;
      up = up + nv - ov;
      up2 = up2 + nv * nv - ov * ov;
    } else {//a new one
      gbsum_cnt[nid] = make_pair(v, 1);
      up = up + v;
      up2 = up2 + v * v;
    }

    double down = gbsum_cnt.size();
    double mm = (down > 0)?up / down:0.0;
    double sm = (down > 0)?up2 / down:0.0;
    double ss = 0;//sigma
    if (down > 1) {
      double adj = (double) (down) / (double)(down - 1);
      ss = sqrt(sm - mm * mm) * sqrt(adj);
    }
    cache[0] = ss;
    cache[1] = up;
    cache[2] = up2;
    double& output = *(sig.GetBasePtr());
    output = cache[0];
    int64_t end_timestamp = TS();
    GLOBAL::macro_seconds_used_by_framework += end_timestamp - start_timestamp;

    std::cout<<"FRAMEWORK((groupbymeanstd)):"<<output<<std::endl;
  }
};

REGISTER(GroupByMeanStd);


class StatSum:public GraphNodeBase
{
  NIO_MATRIX<double> sig;
  double cum_sum;
public:
  void Initialize(const string &para)
  {
    cum_sum = 0;
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<double> &nio_ft = dr->GetData<NIO_MATRIX, double>("volume");
    const double& vol = *(nio_ft.GetBasePtr());

    //each time we get a new qty observation, we need to update cummulative sum
    cum_sum += vol;

    double& output = *(sig.GetBasePtr());

    //output is just the cum_sum
    output = cum_sum;
  }
};

REGISTER(StatSum);

/* @brief HeadLine keeps the header of news
 */
class HeadLine:public GraphNodeBase
{
  NIO_MATRIX<string> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    string& output = *(sig.GetBasePtr());
    output = GLOBAL::global_headline;
  }
};
REGISTER(HeadLine);

/* @brief HeadLine keeps the body of news
 */
class Body:public GraphNodeBase
{
  NIO_MATRIX<string> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    string& output = *(sig.GetBasePtr());
    output = GLOBAL::global_body;
  }

};

REGISTER(Body);


/* @brief if headline is positive result is 1 else 0
 */

class HeadLinePositive:public GraphNodeBase
{
  NIO_MATRIX<int> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<string> &nio_ft = dr->GetData<NIO_MATRIX, string>("headline");
    const string& str = *(nio_ft.GetBasePtr());
    int& output = *(sig.GetBasePtr());
    if (str.find("GOOD") != string::npos) {
      output = 1;
    } else {
      output = 0;
    }
  }

};

REGISTER(HeadLinePositive);


/* @brief if headline is negative result is 1 else 0
 */
class HeadLineNegative:public GraphNodeBase
{
  NIO_MATRIX<int> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<string> &nio_ft = dr->GetData<NIO_MATRIX, string>("headline");
    const string& str = *(nio_ft.GetBasePtr());
    int& output = *(sig.GetBasePtr());
    if (str.find("BAD") != string::npos) {
      output = 1;
    } else {
      output = 0;
    }
  }
};

REGISTER(HeadLineNegative);


/* @brief if body is negative result is 1 else 0
 */

class BodyNegative:public GraphNodeBase
{
  NIO_MATRIX<int> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<string> &nio_ft = dr->GetData<NIO_MATRIX, string>("body");
    const string& str = *(nio_ft.GetBasePtr());
    int& output = *(sig.GetBasePtr());
    if (str.find("BAD") != string::npos) {
      output = 1;
    } else {
      output = 0;
    }
  }

};

REGISTER(BodyNegative);

/* @brief if body is positive result is 1 else 0
 */

class BodyPositive:public GraphNodeBase
{
  NIO_MATRIX<int> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<string> &nio_ft = dr->GetData<NIO_MATRIX, string>("body");
    const string& str = *(nio_ft.GetBasePtr());
    int& output = *(sig.GetBasePtr());
    if (str.find("GOOD") != string::npos) {
      output = 1;
    } else {
      output = 0;
    }
  }
};

REGISTER(BodyPositive);


/* @brief if any event happens(headline positive/negative or body positive/negative) 
 */
class EventMerger:public GraphNodeBase
{
  NIO_MATRIX<int> sig;//merge many VD to VVD
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {

    const NIO_MATRIX<int> &nio_ft1 = dr->GetData<NIO_MATRIX, int>("headline_positive");
    const NIO_MATRIX<int> &nio_ft2 = dr->GetData<NIO_MATRIX, int>("headline_negative");
    const NIO_MATRIX<int> &nio_ft3 = dr->GetData<NIO_MATRIX, int>("body_positive");
    const NIO_MATRIX<int> &nio_ft4 = dr->GetData<NIO_MATRIX, int>("body_negative");

    const int& v1 = *(nio_ft1.GetBasePtr());
    const int& v2 = *(nio_ft2.GetBasePtr());
    const int& v3 = *(nio_ft3.GetBasePtr());
    const int& v4 = *(nio_ft4.GetBasePtr());

    int& output = *(sig.GetBasePtr());
    output = (v1 | v2 | v3 | v4) ?1:0;//if any event happens
  }
};
REGISTER(EventMerger);


/* @brief if any event happens, we dump the timestamp and some feature
 */
class FeatureDumper:public GraphNodeBase
{
  //NIO_MATRIX<int> sig;//merge many VD to VVD
  ofstream out;
public:
  void Initialize(const string &para)
  {
    out.open("DATA/output_from_EXE4.csv", std::ios_base::out);
    assert(!out.fail());
  }
  void LoadData()
  {

    const NIO_MATRIX<int64_t> &nio_ft0 = dr->GetData<NIO_MATRIX, int64_t>("time");
    const NIO_MATRIX<int> &nio_ft1 = dr->GetData<NIO_MATRIX, int>("any_event");
    const NIO_MATRIX<double> &nio_ft2 = dr->GetData<NIO_MATRIX, double>("price_diff");
    const NIO_MATRIX<double> &nio_ft3 = dr->GetData<NIO_MATRIX, double>("price_mean");
    const NIO_MATRIX<double> &nio_ft4 = dr->GetData<NIO_MATRIX, double>("vol_sum");

    const int64_t& v0 = *(nio_ft0.GetBasePtr());
    const int& v1 = *(nio_ft1.GetBasePtr());
    const double& v2 = *(nio_ft2.GetBasePtr());
    const double& v3 = *(nio_ft3.GetBasePtr());
    const double& v4 = *(nio_ft4.GetBasePtr());

    if (v1 == 1) {//some event happened
      out<<v0<<","<<v2<<","<<v3<<","<<v4<<endl;
    }
  }
};
REGISTER(FeatureDumper);


class HourEvent:public GraphNodeBase
{
  NIO_MATRIX<int> sig;//merge many VD to VVD
  int64_t oldti;
public:
  void Dependencies() { }
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {

    const NIO_MATRIX<int64_t> &nio_ft0 = dr->GetData<NIO_MATRIX, int64_t>("time");
    const int64_t& newti = *(nio_ft0.GetBasePtr());

    int& output = *(sig.GetBasePtr());

    if (newti / 3600 != oldti / 3600) {
      output = 1;
    } else {
      output = 0;
    }
    oldti = newti;
  }
};
REGISTER(HourEvent);



class FeatureDumper1:public GraphNodeBase
{
  //NIO_MATRIX<int> sig;//merge many VD to VVD
  ofstream out;
public:
  void Dependencies() { }
  void Initialize(const string &para)
  {
    out.open("DATA/output1_from_EXE4.csv", std::ios_base::out);
    assert(!out.fail());
    //AddDailyData(&sig, tag);
  }
  void LoadData()
  {

    const NIO_MATRIX<int64_t> &nio_ft0 = dr->GetData<NIO_MATRIX, int64_t>("time");
    const NIO_MATRIX<int> &nio_ft1 = dr->GetData<NIO_MATRIX, int>("hour_event");
    const NIO_MATRIX<double> &nio_ft2 = dr->GetData<NIO_MATRIX, double>("price_diff");
    const NIO_MATRIX<double> &nio_ft3 = dr->GetData<NIO_MATRIX, double>("price_mean");
    const NIO_MATRIX<double> &nio_ft4 = dr->GetData<NIO_MATRIX, double>("vol_sum");
    const NIO_MATRIX<double> &nio_ft5 = dr->GetData<NIO_MATRIX, double>("gb");

    const int64_t& v0 = *(nio_ft0.GetBasePtr());
    const int& v1 = *(nio_ft1.GetBasePtr());
    const double& v2 = *(nio_ft2.GetBasePtr());
    const double& v3 = *(nio_ft3.GetBasePtr());
    const double& v4 = *(nio_ft4.GetBasePtr());
    const double& v5 = *(nio_ft5.GetBasePtr());

    if (v1 == 1) {//some event happened
      out<<v0<<","<<v2<<","<<v3<<","<<v4<<","<<v5<<endl;
    }
  }
};
REGISTER(FeatureDumper1);

int main(int argc, char *argv[])
{
  //1. we define the node of the graph, push the name of the node to vector<string>node
  //and push the class name for example TimeLoc(we must inplement) to vector<string> node_class_name
  vector<string> node;
  vector<string> node_class_name;
  node.push_back("time")              ; node_class_name.push_back("TimeLoc")          ;
  node.push_back("volume")            ; node_class_name.push_back("VolumeLoc")        ;
  node.push_back("price")             ; node_class_name.push_back("PriceLoc")         ;
  node.push_back("price_diff")        ; node_class_name.push_back("StatDiff")         ;
  node.push_back("price_mean")        ; node_class_name.push_back("StatMean")         ;
  node.push_back("gb")                ; node_class_name.push_back("GroupByMeanStd")   ;
  node.push_back("vol_sum")           ; node_class_name.push_back("StatSum")          ;
  node.push_back("headline")          ; node_class_name.push_back("HeadLine")         ;
  node.push_back("body")              ; node_class_name.push_back("Body")             ;
  node.push_back("any_event")         ; node_class_name.push_back("EventMerger")      ;
  node.push_back("headline_negative") ; node_class_name.push_back("HeadLineNegative") ;
  node.push_back("headline_positive") ; node_class_name.push_back("HeadLinePositive") ;
  node.push_back("body_negative")     ; node_class_name.push_back("BodyNegative")     ;
  node.push_back("body_positive")     ; node_class_name.push_back("BodyPositive")     ;


  node.push_back("hour_event")        ; node_class_name.push_back("HourEvent")        ;
  node.push_back("feature_dumper")    ; node_class_name.push_back("FeatureDumper")    ;
  node.push_back("feature_dumper1")   ; node_class_name.push_back("FeatureDumper1")   ;
  
  
  //2. create a name to id map, name_to_id[node's name] = node's id in the array
  map<string, int> name_to_id;//map name to id
  for (size_t i = 0;i < node.size();++i) name_to_id[node[i]] = i;
  

  //3. register the dependency, for example str_dependency["price_diff"] = {"price"} 
  //means node price_diff depends on price, we need to calculate price first
  //
  map<string, vector<string>> str_dependency;
  str_dependency["price_diff"] = {"price"};
  str_dependency["price_mean"] = {"price"};
  str_dependency["gb"] = {"price", "volume"};//gb = df[['price', 'volume']].groupby(by='Price').mean().std()
  str_dependency["vol_sum"] = {"volume"};
  str_dependency["headline_negative"] = {"headline"};
  str_dependency["headline_positive"] = {"headline"};
  str_dependency["body_negative"] = {"body"};
  str_dependency["body_positive"] = {"body"};
  str_dependency["any_event"] = {"headline_negative", "headline_positive", "body_negative", "body_positive"};
  str_dependency["feature_dumper"] = {"time", "price_diff", "price_mean", "vol_sum", "any_event"};
  str_dependency["feature_dumper1"] = {"time", "price_diff", "price_mean", "vol_sum", "gb", "hour_event"};




  /*



     

               /-> hour_event--------------------------------->feature_dumper1
              /                           /                               ^
             /                           /                                |
            /                           /                                 |
  time-----/--------------------------------------------------------------|         
                                      /                                   |
  price-->price_diff------------------------------------------------------|          
   \  \                             /                                     |
    \  \->price_mean------------------------------------------------------|       
     \                            /                                       |       
      \----------->gb------------/                                        | 
      /                                                                   |  
     /                                                                    |   
  volume--->vol_sum-------------------------------------------------------|
                                                                          |
                                                                          v
  headline--->headline_negative -----------> any event---------------->feature_dumper
          \                                  ^   ^
           \-->headline_positive -----------/   /
                                               /
  body--->body_negative-----------------------/
          \                                  /
           \-->body_positive----------------/

  */




  //4. use toposort to create correct order of calculation
  vector<set<int>> parents(node.size());
  for (auto &it:str_dependency) {
    int mid = name_to_id.at(it.first);
    for (auto &is:it.second) {
      parents[mid].insert(name_to_id.at(is));
    }
  }
  //get Order
  vector<int> dmgr_order;
  vector<int> dmgr_layer;

  TopoSort(parents, dmgr_order, dmgr_layer);

  for (auto &it:dmgr_order) {
    cout<<it<<endl;
  }



  //5. there are node.size() graph nodes, for each of them, we need to create an object
  //to handle its calculation, we use array dmgr_ptr_ to store their pointers
  //
  std::vector<shared_ptr<GraphNodeBase>> dmgr_ptr_(node.size(), nullptr);
  

  //6. we also need a DataRegister to enable us shared data between different graph nodes
  class DataRegister dr;

  for (int i = 0;i < (int)node.size();++i) {
    //create the object and store its pointer
    dmgr_ptr_[i] = std::static_pointer_cast<GraphNodeBase>(GetClassFromName(node_class_name[i]));
    //set its module id
    dmgr_ptr_[i]->mid = i;
    //tag = each node's name(should be unique)
    dmgr_ptr_[i]->tag = node[i];
    //each node keeps pointer to DataRegister
    dmgr_ptr_[i]->SetDataRegister(&dr);
    //cout<<node[i]<<endl;
  }



  //7. Before start the calculation logic, we need to call the Initialize function for each node.
  //It helps to initialize some states and register the data
  for (size_t i = 0;i < dmgr_order.size();++i) {
    dmgr_ptr_[i]->Initialize("");
  }

  //8. Process each line of data. (In this example, we only deal with AAPL)

  //9. check_price_sum and check_price_cnt we use this variable to calculate the mean price without the framework
  double check_price_sum = 0;
  double check_price_cnt = 0;

  vector<double> prcs_for_debug;
  vector<double> qtys_for_debug;
  

  auto groupbymeanstd = [](vector<double> &prc, vector<double> &qty) ->double{
    map<int, vector<double>> gb;
    for (size_t i = 0;i < prc.size();++i) {
      gb[static_cast<int>(prc[i])].push_back(qty[i]);
    }
    
    vector<double> gb_means;
    for (auto &it:gb) {
      gb_means.push_back(Mean(it.second.begin(), it.second.end()));
    }

    return Sigma(gb_means.begin(), gb_means.end());
  };
  
  ifstream in("DATA/data.csv");
  string ln;
  //10. for each line of data
  while (getline(in, ln)) {//for each of data
    std::vector<std::string> tk = split(ln, ','); 
    //1744246601,GOOG,106,778,BAD header,NEUTRAL body
    string local_ii = (tk[1]);
    if (local_ii != "AAPL") continue;

    //11. extract timestamp,price,qty,headline,body information for AAPL
    GLOBAL::global_timestamp = stoll(tk[0]);
    GLOBAL::global_price = atof(tk[2].c_str());
    GLOBAL::global_qty = atof(tk[3].c_str());
    GLOBAL::global_headline = std::move(tk[4]);
    GLOBAL::global_body = std::move(tk[5]);
    check_price_sum += GLOBAL::global_price;
    check_price_cnt += 1.0;
    cout<<"current timestamp="<<GLOBAL::global_timestamp<<endl;

    //12. update nodes in correct order
    prcs_for_debug.push_back(GLOBAL::global_price);
    qtys_for_debug.push_back(GLOBAL::global_qty);

    for (size_t i = 0;i < dmgr_order.size();++i) {
      int local_mid = dmgr_order[i];
      dmgr_ptr_[local_mid]->LoadData();
    }


    int64_t start_timestamp = TS();
    double db_gbmeanstd = groupbymeanstd(prcs_for_debug, qtys_for_debug);
    int64_t end_timestamp = TS();
    GLOBAL::macro_seconds_used_by_no_framework += end_timestamp - start_timestamp;

    std::cout<<"DO NOT USE FRAMEWORK (groupbymeanstd)="<<db_gbmeanstd<<std::endl;
  }

  std::cout<<"use FRAMEWORK to calculate groupbymeanstd total time = "<<GLOBAL::macro_seconds_used_by_framework<<"us"<<std::endl;
  std::cout<<"do not use FRAMEWORK to calculate groupbymeanstd total time = "<<GLOBAL::macro_seconds_used_by_no_framework<<"us"<<std::endl;
  return 0;
}
