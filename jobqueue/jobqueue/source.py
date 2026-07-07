#!/usr/bin/python
import xmlrpclib
import sys
import time
import pdb


if __name__ == '__main__':
    config = sys.argv[1]
    server = xmlrpclib.Server('http://localhost:16180')
    #joblist = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6'] 
    #joblist = ['cd $HOME/Documents/sima; ./mining_package01/bin/multi_miner -t ' + config] 
    #joblist = ['$HOME/Documents/sima/mining_package01/bin/multi_miner -t $HOME/Documents/sima/' + config] 
    #joblist = ['./mining_package03/bin/mining -config ' + config + ' -type t', './mining_package03/bin/mining -config ' + config + ' -type e']
    jobmap = {}
    jobvals = {}
    
    for job in joblist:
        jid = server.postJob(job)
        jobmap[jid] = job
