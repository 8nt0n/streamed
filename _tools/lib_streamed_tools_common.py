import os
import re
import sys

ARG_VERBOSE = "-v"
LOG_DBG = ARG_VERBOSE in sys.argv
DBG_MSG_PATTERN = re.compile("^\s*\[DBG\]\s")

MEDIA_TYPE_MOVIES = "movies"
MEDIA_TYPE_SERIES = "series"
MEDIA_DIR_PATH = os.path.join("..", "media")

VIDEO_FILE_PATTERN = re.compile("(?i)\\.(mp4|mkv|avi|mpe?g)$")
IMAGE_FILE_PATTERN = re.compile("(?i)\\.(jpe?g|png|gif|svg)$")
FILENAME_REPLACE_PATTERN = re.compile("(?:([a-z])([A-Z]))")
FILENAME_SPLIT_PATTERN = re.compile("[\W_]")

GLOB_SPLI_PATTERN = re.compile("([*?])")

def log(msg):
    if not LOG_DBG and DBG_MSG_PATTERN.search(msg) != None:
        return

    print(msg)


def hasSysArg(argName):
    return argName in sys.argv
    

def findSysArgValue(argName, validator):
    maxArgIdx = len(sys.argv) - 1
    for i in range(1, maxArgIdx):
        if sys.argv[i] == argName and i < maxArgIdx:
            value = sys.argv[i + 1]
            log(f' [DBG] sys arg {argName}={value}')
            return value if validator(value) else None
            
    log(f' [DBG] sys arg {argName} not found')
    return None
        
    
def isVideoFile(path):
    return os.path.isfile(path) and re.search(VIDEO_FILE_PATTERN, path) != None
    

def isImageFile(path):
    return os.path.isfile(path) and re.search(IMAGE_FILE_PATTERN, path) != None


def deleteFile(path):
    try:
        if os.path.isfile(path):
            os.unlink(path)
            log(f" [DBG] file {path} deleted")
    except Exception as ex:
        log(f" [ERR] failed to delete file {path}: {ex}")
    

def fileNameToTitle(path):
    if path == None or len(path.strip()) == 0:
        return None
    
    fileName = os.path.basename(path)
    if len(fileName) == 0:
        return None
    
    tmpStr = VIDEO_FILE_PATTERN.sub("", fileName, 1)
    tmpStr = FILENAME_REPLACE_PATTERN.sub("\\1 \\2", tmpStr) # camelCase handling
    result = ""
    for substr in FILENAME_SPLIT_PATTERN.split(tmpStr):
        if substr == None:
            continue
            
        s = substr.strip()
        length = len(s)
        if length == 0:
            continue
        
        result += substr[0].upper()
        if length > 1:
            result += substr[1:]
            
        result += " "
    
    return result.strip()


def titleToFileName(title, ext = ""):
    return None if title == None else title.lower().replace(" ", "-")
    
    
def patternFromGlob(glob):
    regex = "(?i)"
    for substr in GLOB_SPLI_PATTERN.split(glob):
        if len(substr) == 0:
            continue
        elif substr == "*":
            regex +=".*"
        elif substr == "?":
            regex += "."
        else:
            regex += re.escape(substr)
            
    try:
        log(f" [DBG] GLOB '{glob}' -> regex '{regex}'")
        return re.compile(regex)
    except Exception as ex:
        log(f" [ERR] failed to compile GLOB '{glob}': {ex}")
        raise ex