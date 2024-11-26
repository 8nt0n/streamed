import os
import shutil
import sys

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl

ARG_HELP = "-h"
ARG_HELP_LONG = "--help"
ARG_SRC_FILE = "-s"
ARG_MOVIE_TITLE = "-t"
ARG_MOVIE_DESCR = "-d"
ARG_MEDIA_DIR = "-m"
ARG_CREATE_SYMLINK = "-l"

NOOP_VALIDATOR = lambda argValue: True


def printHelp():
    print(
        f"Usage: python {sys.argv[0]}"
        + f" {ARG_SRC_FILE} <source video path>"
        + f" [{ARG_MEDIA_DIR} <media repository>]"
        + f" [{ARG_MOVIE_TITLE} <movie title>]"
        + f" [{ARG_MOVIE_DESCR} <movie description>]"
        + f" [{ARG_CREATE_SYMLINK}]\n"
        + "This script adds a new video file to the media repository.\n\n"
        + f"Arguments:\n"
        + f"{ARG_SRC_FILE}           path to the source video (mandatory)\n"
        + f"{ARG_MEDIA_DIR}           path to the target media repository containing your streamable movies, defaults to {cmn.MEDIA_DIR_PATH}\n"
        + f"{ARG_MOVIE_TITLE}           the movie's title (will be extracted from the source video file's name if not present)\n"
        + f"{ARG_MOVIE_DESCR}           the movie's description (defaults to the movie's title)\n"
        + f"{ARG_CREATE_SYMLINK}           create a symlink to the source video file instead of copying it to the media repository (must be supported by the operating system) - use with caution!\n"
        + f"{ARG_HELP}, {ARG_HELP_LONG}   print usage information and exit"
    )


def register():
    srcFile = cmn.findSysArgValue(ARG_SRC_FILE, lambda argValue: cmn.isVideoFile(argValue))
    movieTitle = cmn.findSysArgValue(ARG_MOVIE_TITLE, NOOP_VALIDATOR) or cmn.fileNameToTitle(srcFile)
    movieDescr = cmn.findSysArgValue(ARG_MOVIE_DESCR, NOOP_VALIDATOR) or movieTitle
    targetDir = cmn.findSysArgValue(ARG_MEDIA_DIR, lambda argValue: os.path.isdir(argValue)) or cmn.MEDIA_DIR_PATH
    createSymlink = cmn.hasSysArg(ARG_CREATE_SYMLINK) or False
    
    
    cmn.log(f'[INFO] source file: {srcFile}')
    cmn.log(f'[INFO] movie title: {movieTitle}')
    cmn.log(f'[INFO] movie description: {movieDescr}')
    cmn.log(f'[INFO] media repository: {targetDir}')
    cmn.log(f'[INFO] symlink movie: {createSymlink}')
    
    if srcFile == None:
        cmn.log(" [ERR] no valid video file provided")
        sys.exit(-1)

    if targetDir == None or not os.path.isdir(targetDir):
        cmn.log(" [ERR] no valid media repository provided")
        sys.exit(-1)

    # create the movie dir and the 'meta' subfolder
    movieFolder = os.path.join(targetDir, cmn.MEDIA_TYPE_MOVIES, cmn.titleToFileName(movieTitle))
    if os.path.isdir(movieFolder):
        cmn.log(f" [ERR] movie directory '{movieFolder}' already exists")
        sys.exit(-1)
    
    metaFolder = os.path.join(movieFolder, "meta") # TODO: use constant
    os.makedirs(metaFolder)
    if os.path.isdir(metaFolder):
        cmn.log(f" [DBG] directories created: {metaFolder}")
    else:
        cmn.log(f" [ERR] failed to create directory '{metaFolder}'")
        sys.exit(-1)
    
    # copy (or link) video file
    if createSymlink: # TODO: test!!!
        symlinkPath = os.path.join(movieFolder, os.path.basename(srcFile))
        os.symlink(srcFile, symlinkPath)
        cmn.log(f" [DBG] symlink to {srcFile} created: {symlinkPath}")
    else:
        shutil.copy2(srcFile, movieFolder)  # use shutil.copy2() to preserve timestamp
        cmn.log(f" [DBG] {srcFile} copied to {movieFolder}")
    
    # create description text file in the 'meta' subfolder
    descrFilePath = os.path.join(metaFolder, "description.txt") # TODO: use constant
    try:
        with open(descrFilePath, "a") as file:
            file.write(movieDescr)
        
        cmn.log(f" [DBG] description written to {descrFilePath}")
    except Exception as ex:
        cmn.log(f"[WARN] failed to write the description text file {descrFilePath}: {ex}")        
    
    # if possible create thumbnail in the 'meta' subfolder
    
    
    # at last trigger client model refresh
    cmn.log("[INFO] starting client model refresh")
    mdl.refresh()



def main():
    if cmn.hasSysArg(ARG_HELP) or cmn.hasSysArg(ARG_HELP_LONG):
        printHelp()
        sys.exit(0)

    register()
    
    
main()
