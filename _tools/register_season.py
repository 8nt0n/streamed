import glob
import os
import shutil
import sys
import traceback

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl
import lib_register as reg

ARG_HELP = "-h"
ARG_HELP_LONG = "--help"
ARG_SRC_FOLDER = "-f"
ARG_SERIES_TARGET_FOLDER = "-s"
ARG_SEASON_NUMBER = "-n"
ARG_SERIES_TITLE = "-t"
ARG_SERIES_DESCR = "-d"
ARG_RECURSIVE = "-r"
ARG_MEDIA_DIR = "-m"
ARG_SYMLINK = "-l"
ARG_INCL_GLOB = "-i"
ARG_EXCL_GLOB = "-e"

NOOP_VALIDATOR = lambda argValue: True


def printHelp():
    print(
        "Usage:\n"
        + f"python {sys.argv[0]}"
        + f" {ARG_SRC_FOLDER} <source video folder>"
        + f" {ARG_SERIES_TARGET_FOLDER} <series target folder name>"
        + f" [{ARG_SEASON_NUMBER} <season number>]"
        + f" [{ARG_SERIES_TITLE} <series title>]"
        + f" [{ARG_SERIES_DESCR} <series description>]"
        + f" [{ARG_MEDIA_DIR} <media repository>]"
        + f" [{ARG_SYMLINK}]"
        + f" [{ARG_INCL_GLOB} <include files glob>]"
        + f" [{ARG_EXCL_GLOB} <exclude files glob>]"
        + f" [{cmn.ARG_VERBOSE}]\n"

        + "This script adds new episodes of a series to the media repository.\n\n"
        + f"Arguments:\n"
        + f"{ARG_SRC_FOLDER}           path to the folder containing the video files (mandatory when adding multiple movie files to the media repository)\n"
        + f"{ARG_SERIES_TARGET_FOLDER}           name of the target folder in the media repository hosting this series\n"
        + f"{ARG_MEDIA_DIR}           path to the target media repository containing your streamable movies, defaults to {cmn.MEDIA_DIR_PATH}\n"
        + f"{ARG_SERIES_TITLE}           the series' title when adding a season of a new series to the media repository (will be extracted from the series' target folder if not present)\n"
        + f"{ARG_SERIES_DESCR}           the movie's description when adding a single movie file to the media repository (defaults to the series' title)\n"
        + f"{ARG_INCL_GLOB}           include only video files matching the provided GLOB (ignoring case) when processing the source video folder\n"
        + f"{ARG_EXCL_GLOB}           exclude all video files matching the provided GLOB (ignoring case) when processing the source video folder\n"
        + f"{ARG_SYMLINK}           create symlink(s) to the source video files instead of copying them to the media repository (must be supported by the operating system) - use with caution!\n"
        + f"{cmn.ARG_VERBOSE}           enables a more verbose logging\n"
        + f"{ARG_HELP}, {ARG_HELP_LONG}   print usage information and exit\n"
    )
    
    print(
        "Usage examples:\n"
        + "# register (copy) all episodes of the first season of a series:\n"
        + f"python {sys.argv[0]} \\ \n"
        + f" {ARG_SRC_FOLDER} /home/me/videos/rick_morty_season01/ \\ \n"
        + f" {ARG_SERIES_TARGET_FOLDER} rick_and_morty \\ \n"
        + f" {ARG_SERIES_TITLE} \"Rick and Morty\" \\ \n"
        + f" {ARG_SERIES_DESCR} \"\\\"Rick and Morty\\\" is an American animated science fiction sitcom created by Justin Roiland and Dan Harmon.\"\n"
        + "# register (symlink) all episodes of season 8 of an existing (already registered) series:\n"
        + f"python {sys.argv[0]}"
        + f" {ARG_SRC_FOLDER} /home/me/videos/rick_morty_season08/"
        + f" {ARG_SERIES_TARGET_FOLDER} rick_and_morty"
        + f" {ARG_SEASON_NUMBER} 8"
        + f" {ARG_SYMLINK}"
    )
    

def register(srcDir, seriesTargetDir, seasonNum, inclPattern, exclPattern, mediaRepoDir, createSymlink, seriesTitle, seriesDescr):
    targetSeasonDir = os.path.join(mediaRepoDir, "series", seriesTargetDir, seasonNum) # TODO: use constant               
    cmn.makeDirs(targetSeasonDir)
        
    seriesDir = cmn.parentDirOf(targetSeasonDir)
    cmn.log(f" [DBG] series dir: {seriesDir}")
    
    metaFolder = os.path.join(seriesDir, "meta") # TODO: use constant
    cmn.makeDirs(metaFolder)

    # create description text file in the 'meta' subfolder
    descrFilePath = os.path.join(metaFolder, "description.txt") # TODO: use constant
    if not os.path.isfile(descrFilePath):
        seriesDescr = seriesDescr or movieTitle
        try:
            with open(descrFilePath, "a") as file:
                file.write(seriesDescr)
            
            cmn.log(f" [DBG] description written to {descrFilePath}")
        except Exception as ex:
            cmn.log(f"[WARN] failed to write the description text file {descrFilePath}: {ex}")     
            raise ex
    
    episodeNum = 0
    for fsElem in os.listdir(srcDir):
        srcPath = os.path.join(srcDir, fsElem)
        if cmn.isVideoFile(srcPath) and inclPattern.fullmatch(fsElem) != None and exclPattern.fullmatch(fsElem) == None:
            episodeNum = episodeNum + 1
            try:
                reg.registerEpisode(srcPath, targetSeasonDir, mediaRepoDir, episodeNum, createSymlink)
            except Exception as ex:
                cmn.log(f" [ERR] failed to register episodes '{fsElem}': {ex}")
        else:
            cmn.log(f" [DBG] ignoring '{fsElem}' - not a (accepted) video file")


def main():
    if cmn.hasSysArg(ARG_HELP) or cmn.hasSysArg(ARG_HELP_LONG):
        printHelp()
        sys.exit(0)
    
    try:
        srcDir = cmn.findSysArgValue(ARG_SRC_FOLDER, lambda argValue: os.path.isdir(argValue))        
        if srcDir == None:
            raise RuntimeError("no valid source video folder provided")
        
        seriesTargetDir = cmn.findSysArgValue(ARG_SERIES_TARGET_FOLDER, lambda argValue: not os.path.isfile(argValue))
        if seriesTargetDir == None:
            raise RuntimeError("no valid target series folder provided")
        
        seasonNum = cmn.findSysArgValue(ARG_SEASON_NUMBER, lambda argValue: argValue != None and argValue.isdigit()) or "1"
        inclGlob = cmn.findSysArgValue(ARG_INCL_GLOB, NOOP_VALIDATOR) or "*"
        exclGlob = cmn.findSysArgValue(ARG_EXCL_GLOB, NOOP_VALIDATOR) or "." # default: a never matching pattern
        seriesTitle = cmn.findSysArgValue(ARG_SERIES_TITLE, NOOP_VALIDATOR) or cmn.fileNameToTitle(seriesTargetDir)
        seriesDescr = cmn.findSysArgValue(ARG_SERIES_DESCR, NOOP_VALIDATOR) or seriesTitle
        mediaRepoDir = cmn.findSysArgValue(ARG_MEDIA_DIR, lambda argValue: os.path.isdir(argValue)) or cmn.MEDIA_DIR_PATH
        createSymlink = cmn.hasSysArg(ARG_SYMLINK) or False
        
        cmn.log(f"[INFO] source root folder: {srcDir}")
        cmn.log(f"[INFO] series target folder: {seriesTargetDir}")
        cmn.log(f"[INFO] include GLOB: {inclGlob}")
        cmn.log(f"[INFO] exclude GLOB: {exclGlob}")
        cmn.log(f"[INFO] series title: {seriesTitle}")
        cmn.log(f"[INFO] series description: {seriesDescr}")
        cmn.log(f"[INFO] media repository: {mediaRepoDir}")
        cmn.log(f"[INFO] symlink episodes: {createSymlink}")
        
        if mediaRepoDir == None or not os.path.isdir(mediaRepoDir):
            raise RuntimeError("no valid media repository provided")
         
        register(
            srcDir,
            seriesTargetDir,
            seasonNum,
            cmn.patternFromGlob(inclGlob),
            cmn.patternFromGlob(exclGlob),
            mediaRepoDir,
            createSymlink,
            seriesTitle,
            seriesDescr            
        )
            
        # at last trigger client model refresh
        cmn.log("[INFO] starting client model refresh")
        mdl.refresh(False)
    except Exception as ex:    
        cmn.log(f" [ERR] failed to register episodes: {ex}")
        print(traceback.format_exc())
        sys.exit(-1)
    
main()
