import csv
import os
from moviepy.editor import VideoFileClip
import subprocess
import re
import time


def clearfile():
    with open('data.js', 'w') as file:
        pass


def writeData(content, mediatype):
    with open('data.js', 'a') as file:
        file.write("        {\n")
        
        file.write("            title: '")
        file.write(content["name"] + "',\n")
            
        file.write("            path: '")
        file.write(content["path"] + "',\n\n")
        
        if mediatype == "movies":
            file.write("            length: '")
            file.write(content["length"] + "',\n")

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
    with open('data.js', 'a') as file:
        if type == "start":
            file.write("{\n")
        file.write("    var "+ name +" = [\n")

def writeFooter(type):
    with open('data.js', 'a') as file:
            file.write("    ]\n\n")
            if type != "List":
                file.write("}")


class Movie:
    def __init__(self, minute, hour, length):
        self.hour = hour
        self.minute = minute
        self.length = length
    
    def get_length(self, mediapath, path):
        try:
            self.seconds = int(VideoFileClip(f'{mediapath}/{path}/main.mp4').duration) #returns a value in seconds so lets convert that shit to hors minutes
        except:
            self.seconds = int(VideoFileClip(f'{mediapath}/{path}/main.mkv').duration) #returns a value in seconds so lets convert that shit to hors minutes
        #convert seconds to hours
        while self.seconds >= 3600:
            self.hour += 1
            self.seconds -= 3600
        #convert remaining seconds to minutes
        self.minute = self.seconds // 60
        self.length = f'{self.hour}h {self.minute}m'

def get_metainfo(mediapath):

    #get foldername of each movie
    Subfolder = os.listdir(mediapath)
    for i in range(len(Subfolder)):
        DATA = {}

        #check for type
        mediatype = mediapath.replace('media/', '').lower()

        #do the name and path
        path = Subfolder[i]
        name = path.replace('-', ' ')
        DATA["name"] = name
        DATA["path"] = path
        
        #also get length
        if mediatype == "movies":
            my_movie = Movie(0, 0, 0) #pass in random values this language so stupid
            my_movie.get_length(mediapath, path)
            DATA["length"] = my_movie.length

        #looks if description exists  (obviously written by the one and only gpt as if i would write exceptions)
        try:
            with open(mediapath + '/' + path + "/meta/description.txt", "r") as meta:
                # Check if the first line is empty
                line = meta.readline()
                if line == "":
                    print('no description')
                else:
                    DATA["description"] = line
        except FileNotFoundError:
            print('meta/description.txt not found')

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



while True:

    clearfile()

    writeHeader('Movies', type="start") #always call this 1. (argument is the name of the list in js)
    get_metainfo('media/movies') #call all the metainfos 2.and
    writeFooter(type = "List") # always call this last (type = list only places the list footer type != list places the final footer)


    writeHeader('Series', type="anythingBesidesStart")
    get_metainfo('media/Series') #call all the metainfos 2.and
    writeFooter(type = "notList")
    time.sleep(100)
