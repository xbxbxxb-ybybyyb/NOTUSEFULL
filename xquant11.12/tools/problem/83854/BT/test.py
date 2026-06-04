import sys
def getUserDir():
    for i in range(1, len(sys.argv)):
        if (str(sys.argv[i]) == "--user" and i < len(sys.argv)):
            return '/analysis/xquant/' + str(sys.argv[i + 1])
            
print(getUserDir())