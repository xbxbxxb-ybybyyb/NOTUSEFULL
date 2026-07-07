#include "graphnode.h"


void GraphNodeBase::AddDailyData(struct NIO_BASE *niodata, const string &name)
{
  dr->RegisterNiodata(mid, name, niodata);
}
