import os
import sys

def log(msg):
    print(msg)
    

def findSysArgValue(argName, validator):
    maxArgIdx = len(sys.argv) - 1
    for i in range(1, maxArgIdx):
        if sys.argv[i] == argName and i < maxArgIdx:
            value = sys.argv[i + 1]
            log(f' [DBG] sys arg {argName}={value}')
            return value if validator(value) else None
            
    log(f' [DBG] sys arg {argName} not found')
    
def isFile(path):
    return os.path.isfile(path)