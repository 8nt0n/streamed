from collections import Counter
from pathlib import Path
from PIL import Image

import glob
import importlib.util
import io
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
        cmn.deleteFile(tmpFile)
            

# TODO: generally buffer output
def writeData(content, mediatype):

    cmn.log(f"[INFO] '{content['name']}': writing model data of type '{mediatype}' under '{content['path']}'...")

    with io.open(TEMP_FILE_PATH, 'a', encoding='utf8') as file:
        file.write("        {\n")
        
        file.write("            title: '")
        file.write(content["name"] + "',\n")
            
        file.write("            path: '")
        file.write(content["path"] + "',\n")
        
        file.write("            thumbColor: '")
        file.write(content["thumbColor"] + "',\n")
        
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
        
        file.write("            thumbnailFile: '")
        file.write(content["thumbnailFile"] + "',\n")        

        file.write("        },\n")


#always stays the same dummy
def writeHeader(name, type):
    with io.open(TEMP_FILE_PATH, 'a', encoding='utf8') as file:
        if type == "start":
            file.write("{\n")
        file.write("    var " + name + " = [\n")

def writeFooter(type):
    with io.open(TEMP_FILE_PATH, 'a', encoding='utf8') as file:
            file.write("    ]\n\n")
            if type != "List":
                file.write("}")


def infoMapFromMoviepy(mediaFilePath, moviepyModule):
    infoMap = {}
    try:
        with moviepyModule.VideoFileClip(mediaFilePath) as video:
            infoMap['Duration'] = int(video.duration) # returns a value in seconds
            infoMap['Width'] = video.size[0]
            infoMap['Height'] = video.size[1]
    except Exception as ex:
        cmn.log(f' [ERR] failed to examine {mediaFilePath}: {ex}')
        
    return infoMap


def infoMapFromFFProbe(mediaFilePath):
    infoMap = {}
    infoType = "video" # the key to retrieve the video information from the JSON output of the 'ffprobe' command
    try:
        complProc = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', mediaFilePath], capture_output = True)
        jsonMediaObj = json.loads(complProc.stdout)

        infoSections = jsonMediaObj['streams']
        for infos in infoSections:
            if infos['codec_type'] == infoType:
                cmn.log(f" [DBG] found '{infoType}' section in media info for {mediaFilePath}")
                infoMap['Duration'] = round(float(infos['duration'])) # returns a float value in seconds
                infoMap['Width'] = infos['width']
                infoMap['Height'] = infos['height']
                break
    except Exception as ex:
        cmn.log(f" [ERR] failed to run 'ffprobe' (not installed or not in PATH): {ex}")

    return infoMap

    
def infoMapFromMediainfo(mediaFilePath):
    infoType = "Video" # the key to retrieve the video information from the JSON output of the 'mediainfo' command
    try:
        complProc = subprocess.run(['mediainfo', '--Output=JSON', mediaFilePath, '/dev/null'], capture_output = True)
        jsonMediaObj = json.loads(complProc.stdout)

        infoSections = jsonMediaObj[0]['media']['track']
        for infos in infoSections:
            if infos['@type'] == infoType:
                cmn.log(f" [DBG] found '{infoType}' section in media info for {mediaFilePath}")
                return infos
    except Exception as ex:
        cmn.log(f" [ERR] failed to run 'mediainfo' (not installed or not in PATH): {ex}")

    cmn.log(f' [ERR] failed to examine {mediaFilePath}, couldn\'t find \'{infoType}\' section in media info')
    return {}


def thumbnail(videoFilePath, metaDirPath, mediaInfoMap, thumbnailSupplier, forceThumbnailReCreation):
    for file in os.listdir(metaDirPath):
        imgFilePath = os.path.join(metaDirPath, file)
        if cmn.isImageFile(imgFilePath):
            cmn.log(f" [DBG] found thumbnail file {file}")
            if forceThumbnailReCreation:
                cmn.deleteFile(imgFilePath)
            else:
                return file
        else:
            cmn.log(f" [DBG] ignoring {imgFilePath} (not a thumbnail file)")
    
    try:
        #raise RuntimeError("test")
        file = thumbnailSupplier(videoFilePath, metaDirPath, mediaInfoMap)
        cmn.log(f"[INFO] created thumbnail file {file}")
        return file
    except Exception as ex:
        cmn.log(f" [ERR] failed to extract thumbnail file from '{videoFilePath}': {ex} - falling back to SVG...")
        return thumbnailSvg(videoFilePath, metaDirPath)
    
    
def thumbnailSvg(videoFilePath, metaDirPath):
    videoDirPath = Path(videoFilePath).parent
    title = cmn.fileNameToTitle(cmn.parentDirOf(metaDirPath))
    
    svgContent = f'''<?xml version="1.0" encoding="utf-8" standalone="no"?>
    <svg viewBox="0 0 270 150"
        xmlns="http://www.w3.org/2000/svg"
        version="1.1"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xml:lang="de"
        font-size="20" font-family="sans-serif">
      <title>{title}</title>
      <g>
        <text x="30" y="70" textLength="210" lengthAdjust="spacingAndGlyphs" fill="#eee">{title}</text>
      </g>
    </svg>'''      
    thumbnailFile = "thumbnail.svg"
    thumbnailPath = os.path.join(metaDirPath, thumbnailFile)
    cmn.writeTextFile(thumbnailPath, svgContent)

    cmn.log(f"[INFO] created thumbnail file {thumbnailPath}")
    return thumbnailFile


# see e.g. https://www.baeldung.com/linux/ffmpeg-extract-video-frames#extracting-a-single-frame
def thumbnailFromFFMpeg(videoFilePath, metaDirPath, mediaInfoMap):
    thumbnailFile = "thumbnail.jpeg"
    atSecond = str(round(float(mediaInfoMap["Duration"]) / 10))
    complProc = subprocess.run(['ffmpeg', '-i', videoFilePath, '-ss', atSecond, '-vframes', '1', '-q:v', '5', '-s', '220x150', '-v', 'quiet', os.path.join(metaDirPath, thumbnailFile)], capture_output = False)
    return thumbnailFile


def thumbnailBackColor(thumbnailFile):
    try:
        img = Image.open(thumbnailFile).convert("RGB")
        backColorTupel = Counter(img.getdata()).most_common(1)[0][0]
        hexColorStr = f"#{backColorTupel[0]:0{2}x}{backColorTupel[1]:0{2}x}{backColorTupel[2]:0{2}x}"
        cmn.log(f" [DBG] extracted {hexColorStr} '{backColorTupel}' as the 'most common color' from thumbnail file '{thumbnailFile}'")
        return hexColorStr
    except Exception as ex:
        cmn.log(f" [ERR] failed to extract the 'most common color' from thumbnail file '{thumbnailFile}': {ex} - falling back to #000000...")
        return "#000000"
        

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


def get_metainfo(mediatype, mediaInfoExtractor, thumbnailSupplier, forceThumbnailReCreation):
    mediapath = os.path.join(cmn.MEDIA_DIR_PATH, mediatype)
    os.makedirs(mediapath, exist_ok=True) # make sure path exists
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
    
            videoFilePath = os.path.join(videoDirPath, videoFile)

            DATA['path'] = subfolder
            DATA['file'] = videoFile   
            DATA['length'] = UNKNOWN_VALUE
            DATA['resolution'] = UNKNOWN_VALUE            
            DATA['thumbnailFile'] = "dummy.jpg"
            DATA['thumbColor'] = "#ffffff" # TODO: get the 'most common color' from the thumbnail image
            mediaInfo = mediaInfoExtractor(videoFilePath)
            cmn.log(f" [DBG] video infos for {videoFilePath}: {mediaInfo}")
    
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

            thumbnailFile = thumbnail(videoFilePath, os.path.join(videoDirPath, "meta"), mediaInfo, thumbnailSupplier, forceThumbnailReCreation)
            if thumbnailFile != None:
                DATA['thumbnailFile'] = thumbnailFile
                DATA['thumbColor'] = thumbnailBackColor(os.path.join(videoDirPath, "meta", thumbnailFile))
                
        #get Seasons i necessary
        if mediatype == cmn.MEDIA_TYPE_SERIES:           
            #get Episodes
            Seasons = 0
            SeasonsEp = []
            Episodes = 0
            
            videoFilePath = None
            for seasonDirName in cmn.orderedFileList(videoDirPath):
                if seasonDirName != "meta":
#                    Episodes += int(len(os.listdir(mediapath + "/" +  path + "/" + i)))
#                    SeasonsEp.append(int(len(os.listdir(mediapath + "/" +  path + "/" + i))))
                    Seasons += 1
                    episodeVideoFiles = cmn.orderedFileList(os.path.join(videoDirPath, seasonDirName))
                    count = len(episodeVideoFiles)
                    Episodes += count
                    SeasonsEp.append(count)
                    if count > 0 and videoFilePath == None:
                        videoFilePath = os.path.join(videoDirPath, seasonDirName, episodeVideoFiles[0])
            
            DATA["path"] = subfolder
            DATA["Seasons"] = str(Seasons)
            DATA["Episodes"] = str(Episodes)
            DATA["SeasonEp"] = str(SeasonsEp)
            
            if videoFilePath != None:
                mediaInfo = mediaInfoExtractor(videoFilePath)
                thumbnailFile = thumbnail(videoFilePath, os.path.join(videoDirPath, "meta"), mediaInfo, thumbnailSupplier, forceThumbnailReCreation)
                if thumbnailFile != None:
                    DATA['thumbnailFile'] = thumbnailFile
                    DATA['thumbColor'] = thumbnailBackColor(os.path.join(videoDirPath, "meta", thumbnailFile))
            
        DATA["name"] = cmn.fileNameToTitle(subfolder)
        DATA["mediatype"] = mediatype        
        DATA["id"] = str(count)

        # looks if description exists  (obviously written by the one and only gpt as if i would write exceptions)
        try:
            descrPath = os.path.join(mediapath, subfolder, "meta", "description.txt") # TODO: use constants
            descr = cmn.readTextFile(descrPath)
            if descr == "":
                cmn.log(f"[WARN] no description text found in {descrPath}")
                DATA["description"] = ""
            else:
                DATA["description"] = descr.replace("'", "\"").replace("\n", " ").replace("  ", " ")
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
#    return None
    
    name = 'moviepy.editor'
    try:
        if (spec := importlib.util.find_spec(name)) is not None:
            # If you chose to perform the actual import ...
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            cmn.log(f"[INFO] {name!r} module has been imported")
            return module
    except Exception as ex:
        print(f"[INFO] couldn't import {name!r} module: {ex}")

    print(f"[WARN] {name!r} module not available")
    return None



def detectFFProbeVersion():
#    return None

    try:
        complProc = subprocess.run(['ffprobe', '-version', '/dev/null'], capture_output = True)
        vers = complProc.stdout.decode("UTF-8").split('\n', 1)[0]
        cmn.log(f"[INFO] found 'ffprobe' version: {vers}")
        return vers
    except Exception as ex:
        cmn.log(f"[INFO] failed to detect 'ffprobe' version (not installed or not in PATH): {ex}")
        return None


def detectFFMpegVersion():
#    return None

    try:
        complProc = subprocess.run(['ffmpeg', '-version', '/dev/null'], capture_output = True)
        vers = complProc.stdout.decode("UTF-8").split('\n', 1)[0]
        cmn.log(f"[INFO] found 'ffmpeg' version: {vers}")
        return vers
    except Exception as ex:
        cmn.log(f"[INFO] failed to detect 'ffmpeg' version (not installed or not in PATH): {ex}")
        return None


def detectMediainfoVersion():
    return None

    try:
        complProc = subprocess.run(['mediainfo', '--Version', '/dev/null'], capture_output = True)
        vers = complProc.stdout.decode("UTF-8").replace("\r", "").replace("\n", "")
        cmn.log(f"[INFO] found 'mediainfo' version: {vers}")
        return vers
    except Exception as ex:
        cmn.log(f"[INFO] failed to detect 'mediainfo' version (not installed or not in PATH): {ex}")
        return None



def initMediaInfoExtractor():
    if detectMediainfoVersion() != None:
        cmn.log(f"[INFO] using 'mediainfo' command to extract media information")
        mediaInfoExtractor = lambda mediaFilePath: infoMapFromMediainfo(mediaFilePath)
    elif detectFFProbeVersion() != None:
        cmn.log(f"[INFO] using 'ffprobe' command to extract media information")
        mediaInfoExtractor = lambda mediaFilePath: infoMapFromFFProbe(mediaFilePath)
    else:
        moviepyModule = loadMoviepyModule() 
        if moviepyModule != None:
            cmn.log(f"[INFO] using 'moviepy' module to extract media information")
            mediaInfoExtractor = lambda mediaFilePath: infoMapFromMoviepy(mediaFilePath, moviepyModule)
        else:
            cmn.log(f"[WARN] neither 'ffprobe' nor 'mediainfo' nor 'moviepy' module found, extracting media information will not be supported")
            mediaInfoExtractor = lambda mediaFilePath: {}
        
    return mediaInfoExtractor
    
    
def initThumbnailSupplier():    
    if detectFFMpegVersion() != None:
        cmn.log(f"[INFO] using 'ffmpeg' command to extract thumbnail images")
        thumbnailSupplier = lambda mediaFilePath, metaDirPath, mediaInfoMap: thumbnailFromFFMpeg(mediaFilePath, metaDirPath, mediaInfoMap)
    else:
        cmn.log(f"[WARN] 'ffmpeg' not found, fralling back to simple SVG thumbnail generation")
        thumbnailSupplier = lambda mediaFilePath, metaDirPath, mediaInfoMap: thumbnailSvg(mediaFilePath, metaDirPath)
        
    return thumbnailSupplier        



# the actual API (the other stuff is considered to be internal or 'private'):
def refresh(forceThumbnailReCreation):
    cmn.log(" [DBG] clearing old temporary stuff (if there's any)...")
    clearTempData()
    cmn.log(" [DBG] ...done")

    cmn.log(" [DBG] initializing media info extractor...")
    mediaInfoExtractor = initMediaInfoExtractor()
    cmn.log(" [DBG] ...done")
    
    thumbnailSupplier = initThumbnailSupplier()

    writeHeader("Movies", type="start") #always call this 1. (argument is the name of the list in js)
    get_metainfo(cmn.MEDIA_TYPE_MOVIES, mediaInfoExtractor, thumbnailSupplier, forceThumbnailReCreation) #call all the metainfos 2.and
    writeFooter(type = "List") # always call this last (type = list only places the list footer type != list places the final footer)

    writeHeader("Series", type="anythingBesidesStart")
    get_metainfo(cmn.MEDIA_TYPE_SERIES, mediaInfoExtractor, thumbnailSupplier, forceThumbnailReCreation) #call all the metainfos 2.and
    writeFooter(type = "notList")

    os.replace(TEMP_FILE_PATH, DATA_FILE_PATH)
    cmn.log("[INFO] " + DATA_FILE_PATH + " successfully generated")
    
