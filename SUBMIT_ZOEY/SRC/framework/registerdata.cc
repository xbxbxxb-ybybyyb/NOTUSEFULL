#include "registerdata.h"

/* @brief for any graph node, we can register some Nio data(which can be accessed by other graph nodes)
 * @param mid graph node id
 * @param NIO data name
 * @param pointer to the NIO data
 */
void DataRegister::RegisterNiodata(int mid, const std::string &name, struct NIO_BASE *niodata)
{
  if (nioname.count(name) != 0) {
    std::cout<<"repeat name:"<<name<<std::endl;
    throw "(nioname.count(name) != 0)";
  }
  int sz = nioptr.size();
  nioname[name] = sz;
  nioptr.push_back(niodata);
  niomidmp[sz] = mid;
}
