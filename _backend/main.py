import glob
import json
import os
import re
import subprocess
import time
import uuid

MEDIA_TYPE_MOVIES = "movies"
MEDIA_TYPE_SERIES = "series"
MEDIA_DIR_PATH = os.path.join("..", "media")
DATA_FILE_PATH = os.path.join("..", "data.js")
TEMP_FILE_PATH = os.path.join("..", "data_" + uuid.uuid4().hex + ".tmp")
VIDEO_FILE_PATTERN = re.compile("(?i)\\.(mp4|mkv|avi|mpe?g)$")


def clearTempData():
    for tmpFile in glob.glob(os.path.join("..", "data_*.tmp")):
        try:
            if os.path.isfile(tmpFile):
                os.unlink(tmpFile)
                log(f"[INFO] temporary file {tmpFile} deleted")
        except Exception as ex:
            log(f"[WARN] failed to delete temporary file {tmpFile}: {ex}")
            

# TODO: generally buffer output
def writeData(content, mediatype):

    log(f"[INFO] processing {content['name']} of type {mediatype} under {content['path']}...")

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



def collectInfoMap(mediaFilePath, infoType):
#  print(f'::collectInfoMap(\'{mediaFilePath}\', \'{infoType}\')')

    complProc = subprocess.run(['mediainfo', '--Output=JSON', mediaFilePath, '/dev/null'], capture_output = True)
    jsonMediaObj = json.loads(complProc.stdout) 
#    print(jsonMediaObj)

    infoSections = jsonMediaObj[0]['media']['track']
#    print(f'found {len(infoSections)} info sections') 
    for infos in infoSections:
        if infos['@type'] == infoType:
            log(f" [DBG] ::collectInfoMap: found '{infoType}' section in media info for {mediaFilePath}")
            return infos

    log(f" [ERR] ::collectInfoMap: couldn\'t find '{infoType}' section in media info for {mediaFilePath}")
    return []



def findVideoFile(videoDirPath):
    for file in os.listdir(videoDirPath):
        videoFilePath = os.path.join(videoDirPath, file)
        log(f" [DBG] checking {videoFilePath}...")
        if not os.path.isfile(videoFilePath):
            log(f" [DBG] >>> ignoring {videoFilePath} (not a file)")
        elif re.search(VIDEO_FILE_PATTERN, videoFilePath) == None:
            log(f" [DBG] >>> ignoring {videoFilePath} (not a video file)")
        else:
            log(f" [DBG] >>> found video file {file}")
            return file
        
    log(f" [ERR] no supported movie file found in {videoDirPath}")
    return None


def asMovieName(folderName):
    movieName = ""
    for substr in folderName.split("-"):
        s = substr.strip()
        length = len(s)
        if length == 0:
            continue
        
        movieName += substr[0].upper()
        if length > 1:
            movieName += substr[1:]
            
        movieName += " "
    
    return movieName.strip()


def get_metainfo(mediatype):
    mediapath = os.path.join(MEDIA_DIR_PATH, mediatype)
    count = 1
    for subfolder in os.listdir(mediapath):
        DATA = {}

        videoDirPath = os.path.join(mediapath, subfolder)

        if mediatype == MEDIA_TYPE_MOVIES:
            # utilize mediainfo:
            videoFile = findVideoFile(videoDirPath)
            if videoFile == None:
                log(f" [ERR] aborting processing of folder {videoDirPath}")
                continue
                
            
            videoFilePath = os.path.join(videoDirPath, videoFile)

            mediaInfo = collectInfoMap(videoFilePath, 'Video')
            if len(mediaInfo) > 0:
                placeHolder = '[unknown]'
                lengthInfo = placeHolder
                widthInfo = placeHolder
                heightInfo = placeHolder
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
                DATA['path'] = subfolder
                DATA['file'] = videoFile

        #get Seasons i necessary
        if mediatype == MEDIA_TYPE_SERIES:           
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
            
            
        DATA["name"] = asMovieName(subfolder)
        DATA["mediatype"] = mediatype        
        DATA["id"] = str(count)

        # looks if description exists  (obviously written by the one and only gpt as if i would write exceptions)
        try:
            descrPath = os.path.join(mediapath, subfolder, "meta", "description.txt")
            with open(descrPath, "r") as meta:
                # Check if the first line is empty
                line = meta.readline()
                if line == "":
                    log(f"[WARN] no description text found in {descrPath}")
                    DATA["description"] = ""
                else:
                    DATA["description"] = line
        except FileNotFoundError:
            log(f'[WARN] {descrPath} not found')
            
        #write the gathered data to the actual data.js file
#        print(DATA)
#        print("\n\n\n")
        writeData(DATA, mediatype)
        count += 1


def log(msg):
    # TODO: write to log file
    print(msg)


# TODO: provide base directory per script argument (sys.argv[])
def main():
    clearTempData()

    writeHeader("Movies", type="start") #always call this 1. (argument is the name of the list in js)
    get_metainfo(MEDIA_TYPE_MOVIES) #call all the metainfos 2.and
    writeFooter(type = "List") # always call this last (type = list only places the list footer type != list places the final footer)

    writeHeader("Series", type="anythingBesidesStart")
    get_metainfo(MEDIA_TYPE_SERIES) #call all the metainfos 2.and
    writeFooter(type = "notList")

    os.replace(TEMP_FILE_PATH, DATA_FILE_PATH)
    log("[INFO] " + DATA_FILE_PATH + " successfully generated")

main()
