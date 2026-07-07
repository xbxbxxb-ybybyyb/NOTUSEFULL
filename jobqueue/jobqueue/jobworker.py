#!/usr/bin/python
import xmlrpclib
import time
import subprocess
import pdb
import sys
import os

def lastline(filename):
    lastline = ''
    fp = open(filename, 'r')
    for ln in fp:
        ln = ln.strip()
        if (ln == '' or ln == '\n'):
            continue
        lastline = ln
    return lastline

print "Starting up"
server = xmlrpclib.Server("http://localhost:16180")
print "Server found"
myId = server.nextWorkerId()
print "My Worker ID is ",myId

while True:
    print "Waiting for a job"
    jid,para = server.getJob1(myId)
    command = para.split(' ')
    print "====>",command
    #proc = subprocess.Popen(command)
    #proc.wait()

    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    fr = proc.communicate()[0]
    proc.wait()
    ans = []
    ans.append(para)
    for s in fr.split('\n'):
        if (s.find('symlink') == -1 and s.find('rsync') == -1):
            ans.append(s)
    server.postResult(myId,jid, ans)
    print "Posted result"

