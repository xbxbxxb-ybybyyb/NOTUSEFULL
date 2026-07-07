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

/* @brief RandomMat create a random matrix
 */

class RandomMat:public GraphNodeBase
{
  NIO_MATRIX<vector<vector<double>>> sig;
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    vector<vector<double>>& output = *(sig.GetBasePtr());
    int n = 30;
    int m = 3000;
    output = vector<vector<double>>(n, vector<double>(m, 0));//matrix of size n * m
    
    for (int i = 0;i < n;++i) {
      for (int j = 0;j < m;++j) {
        output[i][j] = rand() % 100;//some random number for example
      }
    }
  }
};

REGISTER(RandomMat);


/* @brief RowDemean operator
 */
class RowDemean:public GraphNodeBase
{
  NIO_MATRIX<vector<vector<double>>> sig;//store the demean result
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<vector<vector<double>>> &nio_ft = dr->GetData<NIO_MATRIX, vector<vector<double>>>("randommat");
    const vector<vector<double>>& df = *(nio_ft.GetBasePtr());
    vector<vector<double>>& output = *(sig.GetBasePtr());
    int n = df.size();
    int m = df[0].size();
    output = vector<vector<double>>(n, vector<double>(m, 0));//matrix of size n * m
                      
    for (int i = 0;i < n;++i) {
      double s = 0;
      for (int j = 0;j < m;++j) {
        s += df[i][j];
      }
      s = s / m;//row mean
      for (int j = 0;j < m;++j) {
        output[i][j] = df[i][j] - s;
      }
    }
  }
};

REGISTER(RowDemean);


/* @brief ColDemean operator
 */
class ColDemean:public GraphNodeBase
{
  NIO_MATRIX<vector<vector<double>>> sig;//store the demean result
public:
  void Initialize(const string &para)
  {
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<vector<vector<double>>> &nio_ft = dr->GetData<NIO_MATRIX, vector<vector<double>>>("randommat");
    const vector<vector<double>>& df = *(nio_ft.GetBasePtr());
    vector<vector<double>>& output = *(sig.GetBasePtr());
    int n = df.size();
    int m = df[0].size();
    output = vector<vector<double>>(n, vector<double>(m, 0));//matrix of size n * m
                      
    for (int i = 0;i < m;++i) {
      double s = 0;
      for (int j = 0;j < n;++j) {
        s += df[j][i];
      }
      s = s / m;//row mean
      for (int j = 0;j < n;++j) {
        output[j][i] = df[j][i] - s;
      }
    }
  }
};

REGISTER(ColDemean);





/* @brief ABSSUM op
 */
class ABSSUM:public GraphNodeBase
{
  NIO_MATRIX<vector<double>> sig;//vector<double> to store alphas
  string dep;
public:
  void Initialize(const string &para)
  {
    dep = para;//make dependency as a parameter
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<vector<vector<double>>> &nio_ft = dr->GetData<NIO_MATRIX, vector<vector<double>>>(dep.c_str());
    const vector<vector<double>>& df = *(nio_ft.GetBasePtr());
    vector<double>& output = *(sig.GetBasePtr());
    int n = df.size();
    int m = df[0].size();
    output = vector<double>(m, 0);//vector of size m
                      
    for (int i = 0;i < m;++i) {
      double s = 0;
      for (int j = 0;j < n;++j) {
        s += abs(df[j][i]);
      }
      output[i] = s;
    }
  }
};

REGISTER(ABSSUM);


/* @brief SQUARESUM op
 */
class SQUARESUM:public GraphNodeBase
{
  NIO_MATRIX<vector<double>> sig;//vector<double> to store alphas
  string dep;
public:
  void Initialize(const string &para)
  {
    dep = para;//make dependency as a parameter
    AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<vector<vector<double>>> &nio_ft = dr->GetData<NIO_MATRIX, vector<vector<double>>>(dep.c_str());
    const vector<vector<double>>& df = *(nio_ft.GetBasePtr());
    vector<double>& output = *(sig.GetBasePtr());
    int n = df.size();
    int m = df[0].size();
    output = vector<double>(m, 0);//vector of size m
                      
    for (int i = 0;i < m;++i) {
      double s = 0;
      for (int j = 0;j < n;++j) {
        s += df[j][i] * df[j][i];
      }
      output[i] = s;
    }
  }
};

REGISTER(SQUARESUM);




/* @brief TOCSV
 */
class TOCSV:public GraphNodeBase
{
  //NIO_MATRIX<vector<double>> sig;//vector<double> to store alphas

public:
  void Initialize(const string &para)
  {
    //AddDailyData(&sig, tag);
  }
  void LoadData()
  {
    const NIO_MATRIX<vector<double>> &nio_ft0 = dr->GetData<NIO_MATRIX, vector<double>>("mat1_abssum");
    const NIO_MATRIX<vector<double>> &nio_ft1 = dr->GetData<NIO_MATRIX, vector<double>>("mat1_squaresum");
    const NIO_MATRIX<vector<double>> &nio_ft2 = dr->GetData<NIO_MATRIX, vector<double>>("mat2_abssum");
    const NIO_MATRIX<vector<double>> &nio_ft3 = dr->GetData<NIO_MATRIX, vector<double>>("mat2_squaresum");

    const vector<double>& alpha0 = *(nio_ft0.GetBasePtr());
    const vector<double>& alpha1 = *(nio_ft1.GetBasePtr());
    const vector<double>& alpha2 = *(nio_ft2.GetBasePtr());
    const vector<double>& alpha3 = *(nio_ft3.GetBasePtr());

    ofstream out("DATA/output_from_EXE5.csv");
    out<<",mat1_abssum,mat1_squaresum,mat2_abssum,mat2_squaresum"<<endl;

    int n = alpha0.size();
    for (int i = 0;i < n;++i) {
      out<<i<<","<<alpha0[i]<<","<<alpha1[i]<<","<<alpha2[i]<<","<<alpha3[i]<<endl;
    }
  }
};

REGISTER(TOCSV);



int main(int argc, char *argv[])
{
  //1. we define the node of the graph, push the name of the node to vector<string>node
  //and push the class name for example TimeLoc(we must inplement) to vector<string> node_class_name
  vector<string> node;
  vector<string> node_class_name;
  node.push_back("randommat")       ; node_class_name.push_back("RandomMat")     ;
  node.push_back("mat1")           ; node_class_name.push_back("RowDemean") ;
  node.push_back("mat2")           ; node_class_name.push_back("ColDemean") ;

  node.push_back("mat1_abssum")    ; node_class_name.push_back("ABSSUM")    ;
  node.push_back("mat1_squaresum") ; node_class_name.push_back("SQUARESUM") ;
  node.push_back("mat2_abssum")    ; node_class_name.push_back("ABSSUM")    ;
  node.push_back("mat2_squaresum") ; node_class_name.push_back("SQUARESUM") ;

  node.push_back("tocsv")          ; node_class_name.push_back("TOCSV")     ;

  
  //2. create a name to id map, name_to_id[node's name] = node's id in the array
  map<string, int> name_to_id;//map name to id
  for (size_t i = 0;i < node.size();++i) name_to_id[node[i]] = i;
  

  //3. register the dependency, for example str_dependency["price_diff"] = {"price"} 
  //means node price_diff depends on price, we need to calculate price first
  //
  map<string, vector<string>> str_dependency;
  str_dependency["mat1"] = {"randommat"};
  str_dependency["mat2"] = {"randommat"};

  str_dependency["mat1_abssum"] = {"mat1"};
  str_dependency["mat2_abssum"] = {"mat2"};

  str_dependency["mat1_squaresum"] = {"mat1"};
  str_dependency["mat2_squaresum"] = {"mat2"};

  str_dependency["tocsv"] = {"mat1_abssum", "mat2_abssum", "mat1_squaresum", "mat2_squaresum"};



  /*

     randommat-->mat1-->mat1_squaresum------->tocsv
              |      \->mat1_abssum---------/
              |->mat2-->mat2_squaresum-----/
                     \->mat2_abssum-------/

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



  //node.push_back("randommat")      
  //node.push_back("mat1")           
  //node.push_back("mat2")           
  //node.push_back("mat1_abssum")    
  //node.push_back("mat1_squaresum") 
  //node.push_back("mat2_abssum")    
  //node.push_back("mat2_squaresum") 
  //node.push_back("tocsv")          

  vector<string> paras = {"","", "", "mat1", "mat1", "mat2", "mat2", ""};




  //7. Before start the calculation logic, we need to call the Initialize function for each node.
  //It helps to initialize some states and register the data
  for (size_t i = 0;i < dmgr_order.size();++i) {
    dmgr_ptr_[i]->Initialize(paras[i].c_str());
  }


  for (size_t i = 0;i < dmgr_order.size();++i) {
    int local_mid = dmgr_order[i];
    dmgr_ptr_[local_mid]->LoadData();
    cout<<"building:"<<dmgr_ptr_[local_mid]->tag<<endl;
  }


  return 0;
}
