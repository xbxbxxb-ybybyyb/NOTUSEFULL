#!/usr/bin/python
import xmlrpc.client    #导入模块
import sys
import time
import pdb


if __name__ == '__main__':
    dmgr = sys.argv[1]
    server = xmlrpc.client.ServerProxy('http://localhost:16182') 
    joblist = ['ls']
    jobmap = {}
    jobvals = {}
    
    for job in joblist:
        jid = server.postJob(job)
        jobmap[jid] = job
