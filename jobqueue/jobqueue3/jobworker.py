#!/usr/bin/python3
import time
import xmlrpc.client
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

print("Starting up")
server = xmlrpc.client.ServerProxy('http://localhost:16182') 
print("Server found")
myId = server.nextWorkerId()
print("My Worker ID is " + str(myId))

while True:
    print("Waiting for a job")
    jid,para = server.getJob1(myId)
    command = para.split(' ')
    print("command====>",command)
    print("para====>",para)

    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    fr = proc.communicate()[0]
    proc.wait()
    ans = []
    ans.append(para)
    for s in fr.split(b'\n'):
        ans.append(str(s, encoding = "utf8"))
    
    server.postResult(myId,jid, ans)
    print("Posted result")
