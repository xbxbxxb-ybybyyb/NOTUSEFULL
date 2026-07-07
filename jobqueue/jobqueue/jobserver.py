#!/usr/bin/python

#http://www.ironalbatross.net/wiki/index.php5/Simple_Job_Queue

import SocketServer
import SimpleXMLRPCServer
import threading
from Queue import Queue
from Queue import Empty

def idMaker():
    id = 1
    while True:
        yield id
        id += 1

class JobQueue:
    nextWorkerId = idMaker().next
    nextJobId = idMaker().next
    inQueue = Queue()
    outQueue = Queue()
    pending = {}
    def postJob(self,job):
        print "postJob"
        jid = self.nextJobId()
        self.inQueue.put( (jid,job) )
        print "Recieved job:",job
        return jid
    def getJob1(self,myId):
        print "getJob"
        jid,job = self.inQueue.get()
        self.pending[jid] = job
        print "Delegated job:",job
        return jid,job
    #def postResult(self,myId,jid,value):
    def postResult(self,myId,jid, job):
        print "postResult"
        print job
        if self.pending.has_key(jid):
            del self.pending[jid]
            self.outQueue.put( (jid,job) )
            print "Job was finished"
        else:
            print "Serious error has occured"
        return True
    def getResult(self):
        print "getResult"
        val = self.outQueue.get()
        print "Result was sent"
        return val
class AsyncXMLRPCServer(SocketServer.ThreadingMixIn,
                        SimpleXMLRPCServer.SimpleXMLRPCServer): pass
if __name__=="__main__":
    server = AsyncXMLRPCServer(("localhost",16180))
    server.register_instance(JobQueue())
    server.serve_forever()
