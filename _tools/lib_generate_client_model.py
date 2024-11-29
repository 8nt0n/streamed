import glob
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import uuid

import lib_streamed_tools_common as cmn


DATA_FILE_PATH = os.path.join("..", "data.js")
TEMP_FILE_PATH = os.path.join("..", "data_" + uuid.uuid4().hex + ".tmp")
UNKNOWN_VALUE = "[n/a]"

def clearTempData():
    for tmpFile in glob.glob(os.path.join("..", "data_*.tmp")):
        try:
            if os.path.isfile(tmpFile):
                os.unlink(tmpFile)
                cmn.log(f"[INFO] temporary file {tmpFile} deleted")
        except Exception as ex:
            cmn.log(f"[WARN] failed to delete temporary file {tmpFile}: {ex}")
            

# TODO: generally buffer output
def writeData(content, mediatype):

    cmn.log(f"[INFO] \'{content['name']}\': writing model data of type \'{mediatype}\' under \'{content['path']}\'...")

    with open(TEMP_FILE_PATH, 'a') as file:
        file.write("        {\n")
        
        file.write("            title: '")
        file.write(content["name"] + "',\n")
            
        file.write("            path: '")
        file.write(content["path"] + "',\n")
        
        if mediatype == "movies":
            file.write("            file: '")
            file.write(content["file"] + "',\n")        
        
            file.write("            length: '")
            file.write(content["length"] + "',\n")

            file.write("            resolution: '")
            file.write(content["resolution"] + "',\n")

            file.write("            description: '")
            file.write(content["description"] + "',\n\n")
        elif mediatype == "series":
            file.write("            seasons: '")
            file.write(content["Seasons"] + "',\n")

            file.write("            episodes: '")
            file.write(content["Episodes"] + "',\n")

            file.write("            seasonEp: ")
            file.write(content["SeasonEp"] + ",\n")
            
            file.write("            description: '")
            file.write(content["description"] + "',\n\n")


        file.write("            type: '")
        file.write(content["mediatype"] + "',\n")

        file.write("            id: '")
        file.write(content["id"] + "',\n")

        file.write("        },\n")


#always stays the same dummy
def writeHeader(name, type):
    with open(TEMP_FILE_PATH, 'a') as file:
        if type == "start":
            file.write("{\n")
        file.write("    var " + name + " = [\n")

def writeFooter(type):
    with open(TEMP_FILE_PATH, 'a') as file:
            file.write("    ]\n\n")
            if type != "List":
                file.write("}")



def collectInfoMap(mediaFilePath, infoType, moviepyModule):
    if moviepyModule is not None:
        cmn.log(f' [DBG] trying to extract movie meta data using moviepy...')
        return infoMapFromMoviepy(mediaFilePath, moviepyModule)
    else:
        cmn.log(f' [DBG] trying to extract movie meta data using mediainfo command...')
        return infoMapFromMediainfo(mediaFilePath, infoType)
    

def infoMapFromMoviepy(mediaFilePath, moviepyModule):
    infoMap = {}
    try:
        with moviepyModule.VideoFileClip(mediaFilePath) as video:
            infoMap['Duration'] = int(video.duration) #returns a value in seconds
#            cmn.log(f' [DBG] video.size={video.size}')
            infoMap['Width'] = video.size[0]
            infoMap['Height'] = video.size[1]
    except Exception as ex:
        cmn.log(f' [ERR] failed to examine {mediaFilePath}: {ex}')
        
    cmn.log(f' [DBG] video infos for {mediaFilePath}: {infoMap}')
        
    return infoMap
    
    
    
def infoMapFromMediainfo(mediaFilePath, infoType):
    try:
        complProc = subprocess.run(['mediainfo', '--Output=JSON', mediaFilePath, '/dev/null'], capture_output = True)
        jsonMediaObj = json.loads(complProc.stdout) 
#        print(jsonMediaObj)

        infoSections = jsonMediaObj[0]['media']['track']
#        print(f'found {len(infoSections)} info sections') 
        for infos in infoSections:
            if infos['@type'] == infoType:
                cmn.log(f" [DBG] found '{infoType}' section in media info for {mediaFilePath}")
#                cmn.log(f' [DBG] video infos for {mediaFilePath}: {infos}')
                return infos
    except Exception as ex:
        cmn.log(f" [ERR] failed to run 'mediainfo' (not installed or not in PATH): {ex}")

    cmn.log(f' [ERR] failed to examine {mediaFilePath}, couldn\'t find \'{infoType}\' section in media info')
    return {}



def findVideoFile(videoDirPath):
    for file in os.listdir(videoDirPath):
        videoFilePath = os.path.join(videoDirPath, file)
#        cmn.log(f" [DBG] checking {videoFilePath}...")
        if not cmn.isVideoFile(videoFilePath):
            cmn.log(f" [DBG] ignoring {videoFilePath} (not a video file)")
        else:
            cmn.log(f"[INFO] found video file {file}")
            return file
        
    cmn.log(f" [ERR] no supported movie file found in {videoDirPath}")
    return None


def get_metainfo(mediatype, moviepyModule):
    mediapath = os.path.join(cmn.MEDIA_DIR_PATH, mediatype)
    count = 1    
    for subfolder in os.listdir(mediapath):
        DATA = {}

        videoDirPath = os.path.join(mediapath, subfolder)
        if not os.path.isdir(videoDirPath):
            continue

        if mediatype == cmn.MEDIA_TYPE_MOVIES:
            # utilize mediainfo:
            videoFile = findVideoFile(videoDirPath)
            if videoFile == None:
                cmn.log(f" [ERR] aborting processing of folder {videoDirPath}")
                continue
            
            DATA['path'] = subfolder
            DATA['file'] = videoFile   
            DATA['length'] = UNKNOWN_VALUE
            DATA['resolution'] = UNKNOWN_VALUE
                
            videoFilePath = os.path.join(videoDirPath, videoFile)
            mediaInfo = collectInfoMap(videoFilePath, 'Video', moviepyModule)
            if len(mediaInfo) > 0:
                lengthInfo = UNKNOWN_VALUE
                widthInfo = UNKNOWN_VALUE
                heightInfo = UNKNOWN_VALUE
                for name in mediaInfo:
                    if name == 'Duration':
                        seconds = float(mediaInfo[name])
                        h = int(seconds / 3600)
                        m = int((seconds % 3600) / 60)
                        minutes = "{:02d}".format(m) if h > 0 else str(m)
                        lengthInfo = f'{h}:{minutes} h' if h > 0 else f'{minutes} min'
                    elif name == 'Width':
                        widthInfo = mediaInfo[name]
                    elif name == 'Height':
                        heightInfo = mediaInfo[name]
                # store the detected values in the model:
                DATA['length'] = lengthInfo
                DATA['resolution'] = f'{widthInfo}x{heightInfo} px'
                
        #get Seasons i necessary
        if mediatype == cmn.MEDIA_TYPE_SERIES:           
            #get Episodes
            Seasons = 0
            SeasonsEp = []
            Episodes = 0
            for i in os.listdir(videoDirPath):
                if i != "meta":
#                    Episodes += int(len(os.listdir(mediapath + "/" +  path + "/" + i)))
#                    SeasonsEp.append(int(len(os.listdir(mediapath + "/" +  path + "/" + i))))
                    Seasons += 1
                    count = len(os.listdir(os.path.join(videoDirPath, i)))
                    Episodes += count
                    SeasonsEp.append(count) # TODO: check order of 'listDir' result
            
            DATA["path"] = subfolder
            DATA["Seasons"] = str(Seasons)
            DATA["Episodes"] = str(Episodes)
            DATA["SeasonEp"] = str(SeasonsEp)
            
            
        DATA["name"] = cmn.fileNameToTitle(subfolder)
        DATA["mediatype"] = mediatype        
        DATA["id"] = str(count)

        # looks if description exists  (obviously written by the one and only gpt as if i would write exceptions)
        try:
            descrPath = os.path.join(mediapath, subfolder, "meta", "description.txt") # TODO: use constants
            with open(descrPath, "r") as meta:
                # Check if the first line is empty
                line = meta.readline()
                if line == "":
                    cmn.log(f"[WARN] no description text found in {descrPath}")
                    DATA["description"] = ""
                else:
                    DATA["description"] = line
        except FileNotFoundError:
            cmn.log(f'[WARN] {descrPath} not found')
            
        #write the gathered data to the actual data.js file
#        print(DATA)
#        print("\n\n\n")
        writeData(DATA, mediatype)
        count += 1

    

# imports moviepy if it's available, see https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported    
# install with:
# pip install --force-reinstall -v "moviepy==1.0.3"
def loadMoviepyModule():
#    if True:
#        return None
        
    name = 'moviepy.editor'
    try:
        if (spec := importlib.util.find_spec(name)) is not None:
            # If you chose to perform the actual import ...
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            cmn.log(f"[INFO] {name!r} has been imported")
            return module
    except Exception as ex:
        print(f" [ERR] couldn't import {name!r} module: {ex}")

    print(f"[WARN] {name!r} module not available")
    return None


def detectMediainfoVersion():
    try:
        complProc = subprocess.run(['mediainfo', '--Version', '/dev/null'], capture_output = True)
        vers = complProc.stdout.decode("UTF-8").replace("\r", "").replace("\n", "")
        cmn.log(f"[INFO] found 'mediainfo' version: {vers}")
        return vers
    except Exception as ex:
        cmn.log(f" [ERR] failed to detect 'mediainfo' version (not installed or not in PATH): {ex}")
        return None


# main entry point:
def refresh():
    clearTempData()
        
    moviepyModule = loadMoviepyModule()
    if moviepyModule != None:
        cmn.log(f"[INFO] using 'moviepy' module to extract media information")
    elif detectMediainfoVersion() != None:
        cmn.log(f"[INFO] using 'mediainfo' command to extract media information")
    else:
        # TODO: also try ffmpeg
        cmn.log(f"[WARN] neither 'moviepy' module nor 'mediainfo' found, extracting media information will not be supported")
    
    writeHeader("Movies", type="start") #always call this 1. (argument is the name of the list in js)
    get_metainfo(cmn.MEDIA_TYPE_MOVIES, moviepyModule) #call all the metainfos 2.and
    writeFooter(type = "List") # always call this last (type = list only places the list footer type != list places the final footer)

    writeHeader("Series", type="anythingBesidesStart")
    get_metainfo(cmn.MEDIA_TYPE_SERIES, moviepyModule) #call all the metainfos 2.and
    writeFooter(type = "notList")

    os.replace(TEMP_FILE_PATH, DATA_FILE_PATH)
    cmn.log("[INFO] " + DATA_FILE_PATH + " successfully generated")
