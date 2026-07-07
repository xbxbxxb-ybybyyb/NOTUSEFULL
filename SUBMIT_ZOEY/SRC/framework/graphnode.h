#pragma once
#include<string>
#include "registerdata.h"

/*
 * @brief this is an abstract class, users need to inherit from it to create their own computational logic
 *
 */
class GraphNodeBase
{
  public:
    class DataRegister *dr;//pointer to data register
    std::string tag;//the name of each node
    int mid;//module id
    GraphNodeBase() {}

    /*
     * @brief this is a virtual function, user need to use it to initialize each node 
     * @param para is string, we can pass some parameter or ""
     */
    virtual void Initialize(const string &para) = 0;

    /*
     * @brief this is a virtual function, user need to implement the calculation logic here
     * @param para is string, we can pass some parameter or ""
     */
    virtual void LoadData() = 0;

    /*
     * @brief this function help to register graphnode's local variable, so that it can be used by other nodes
     * @param niodata pointer to some data
     * @param name can be used as a key, we can used this name as key(so that from other nodes we can used this key to find this node's data)
     */
    void AddDailyData(struct NIO_BASE *niodata, const string &name);

    /*
     * @brief each node keep's the pointer to a common DataRegister
     *
     */
    void SetDataRegister(class DataRegister * drptr) {dr = drptr;}
};


