import json
import os
import re
import subprocess
import time

MEDIA_DIR_PATH = "../media"
DATA_FILE_PATH = "../data.js"
TEMP_FILE_PATH = "../data.tmp"

# TODO: generally buffer output
def writeData(content, mediatype):

    print(f'processing {mediatype} {content["name"]} under  {content["path"]}...')

    with open(TEMP_FILE_PATH, 'a') as file:
        file.write("        {\n")
        
        file.write("            title: '")
        file.write(content["name"] + "',\n")
            
        file.write("            path: '")
        file.write(content["path"] + "',\n\n")
        
        if mediatype == "movies":
            file.write("            length: '")
            file.write(content["length"] + "',\n")

            file.write("            resolution: '")
            file.write(content["resolution"] + "',\n")

            file.write("            description: '")
            file.write(content["description"] + "',\n\n")

        if mediatype == "series":
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
        file.write("    var "+ name +" = [\n")

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
            print(f'found "{infoType}" section')
            return infos

    log(f'[ ERR] couldn\'t find "{infoType}" section')
    return []



def get_metainfo(mediapath):

    #get foldername of each movie
    Subfolder = os.listdir(mediapath)
    for i in range(len(Subfolder)):
        DATA = {}

        #check for type
        mediatype = mediapath.replace(MEDIA_DIR_PATH + "/", '').lower()

        #do the name and path
        path = Subfolder[i]
        name = path.replace('-', ' ')
        DATA["name"] = name
        DATA["path"] = path

        #also get length
        if mediatype == "movies":
#            my_movie = Movie(0, 0, 0) #pass in random values this language so stupid
#            my_movie.get_length(mediapath, path)
#            DATA["length"] = my_movie.length

            # utilize mediainfo:
            videoDirPath = mediapath + '/' + path
            videoFilePath = videoDirPath + '/main.mp4'
            if  not os.path.isfile(videoFilePath):
                videoFilePath = videoDirPath + '/main.mkv' # ahem...

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

        # looks if description exists  (obviously written by the one and only gpt as if i would write exceptions)
        try:
            descrPath = mediapath + '/' + path + "/meta/description.txt"
            with open(descrPath, "r") as meta:
                # Check if the first line is empty
                line = meta.readline()
                if line == "":
                    print('no description')
                else:
                    DATA["description"] = line
        except FileNotFoundError:
            log(f'[WARN] {descrPath} not found')

        DATA["mediatype"] = mediatype
        
        #get id
        id =  mediatype[0].upper() + str(i+1)
        DATA["id"] = id

        
        #get Seasons i necessary
        if mediatype == "series":
            Seasons = str(len(os.listdir(mediapath + "/" +  path)) -1) #-1 bc of the meta folder
            DATA["Seasons"] = Seasons

            #get Episodes
            SeasonsEp = []
            Episodes = 0
            for i in os.listdir(mediapath + "/" +  path):
                if i != "meta":
                    Episodes += int(len(os.listdir(mediapath + "/" +  path + "/" + i)))
                    SeasonsEp.append(int(len(os.listdir(mediapath + "/" +  path + "/" + i))))
            DATA["Episodes"] = str(Episodes)
            DATA["SeasonEp"] = str(SeasonsEp)
        #write the gathered data to the actual data.js file
        print(DATA)
        print("\n\n\n")
        writeData(DATA, mediatype)


def log(msg):
    # TODO: write to log file
    print(msg)


# TODO: provide base directory per script argument (sys.argv[])
def main():

    writeHeader('Movies', type="start") #always call this 1. (argument is the name of the list in js)
    get_metainfo(MEDIA_DIR_PATH + '/movies') #call all the metainfos 2.and
    writeFooter(type = "List") # always call this last (type = list only places the list footer type != list places the final footer)

    writeHeader('Series', type="anythingBesidesStart")
    get_metainfo(MEDIA_DIR_PATH + '/series') #call all the metainfos 2.and
    writeFooter(type = "notList")

    os.replace(TEMP_FILE_PATH, DATA_FILE_PATH)
    log("[INFO] " + DATA_FILE_PATH + " successfully generated")

main()
