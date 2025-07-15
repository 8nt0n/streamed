import glob
import os
import shutil
import sys

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl
import lib_register as reg

ARG_HELP = "-h"
ARG_HELP_LONG = "--help"
ARG_SRC_FILE = "-s"
ARG_SRC_FOLDER = "-f"
ARG_MOVIE_NAME = "-n"
ARG_MOVIE_DESCRIPTION = "-d"
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
        + f" {ARG_SRC_FILE} <source video file>"
        + f" [{ARG_MOVIE_NAME} <movie name>]"
        + f" [{ARG_MOVIE_DESCRIPTION} <movie description>]"
        + f" [{ARG_MEDIA_DIR} <media repository>]"
        + f" [{ARG_SYMLINK}]"
        + f" [{cmn.ARG_VERBOSE}]\n"
        + f"python {sys.argv[0]}"
        + f" {ARG_SRC_FOLDER} <source video folder>"
        + f" [{ARG_RECURSIVE}]"
        + f" [{ARG_MEDIA_DIR} <media repository>]"
        + f" [{ARG_INCL_GLOB} <include files glob>]"
        + f" [{ARG_EXCL_GLOB} <exclude files glob>]"
        + f" [{ARG_SYMLINK}]"
        + f" [{cmn.ARG_VERBOSE}]\n"

        + "This script adds new video files to the media repository.\n\n"
        + f"Arguments:\n"
        + f"{ARG_SRC_FILE}           path to the source video (mandatory when adding a single movie file to the media repository)\n"
        + f"{ARG_SRC_FOLDER}           path to the folder containing the video files (mandatory when adding multiple movie files to the media repository)\n"
        + f"{ARG_MEDIA_DIR}           path to the target media repository containing your streamable movies, defaults to {cmn.MEDIA_DIR_PATH}\n"
        + f"{ARG_MOVIE_NAME}           the movie's title when adding a single movie file to the media repository (will be extracted from the source video file's name if not present)\n"
        + f"{ARG_MOVIE_DESCRIPTION}           the movie's description when adding a single movie file to the media repository, may be a string or a text file (defaults to the movie's title)\n"
        + f"{ARG_INCL_GLOB}           include only video files matching the provided GLOB (ignoring case) when processing the source video folder\n"
        + f"{ARG_EXCL_GLOB}           exclude all video files matching the provided GLOB (ignoring case) when processing the source video folder\n"
        + f"{ARG_RECURSIVE}           include all subfolders when processing the source video folder - use with caution!\n"
        + f"{ARG_SYMLINK}           create symlinks to the source video files instead of copying them to the media repository (must be supported by the operating system) - use with caution!\n"
        + f"{cmn.ARG_VERBOSE}           enables a more verbose logging\n"
        + f"{ARG_HELP}, {ARG_HELP_LONG}   print usage information and exit\n"
    )
    
    print(
        "Usage examples:\n"
        + "# register (copy) a single movie file:\n"
        + f"python {sys.argv[0]} \\ \n"
        + f" {ARG_SRC_FILE} /home/me/videos/blues_brothers.mp4 \\ \n"
        + f" {ARG_MOVIE_NAME} \"The Blues Brothers\" \\ \n"
        + f" {ARG_MOVIE_DESCRIPTION} \"\\\"The Blues Brothers\\\" is a 1980 American musical action comedy film directed by John Landis with John Belushi and Dan Aykroyd.\"\n"
        + "# register (symlink) all of the movie files located in the provided folder and its subfolders:\n"
        + f"python {sys.argv[0]}"
        + f" {ARG_SRC_FOLDER} /home/me/videos/"
        + f" {ARG_RECURSIVE}"
        + f" {ARG_SYMLINK}\n"
        + "# register (symlink) all MP4 movie files located in the provided folder without 'blue' in their file name:\n"
        + f"python {sys.argv[0]}"
        + f" {ARG_SRC_FOLDER} /home/me/videos/"
        + f" {ARG_INCL_GLOB} *.mp4"
        + f" {ARG_EXCL_GLOB} *blue*"
        + f" {ARG_SYMLINK}"
    )
    

def registerFolder(dir, inclPattern, exclPattern, recursive, targetDir, createSymlink):
    for fsElem in os.listdir(dir):
        path = os.path.join(dir, fsElem)
        if cmn.isVideoFile(path) and inclPattern.fullmatch(fsElem) != None and exclPattern.fullmatch(fsElem) == None:
            try:
                movieTitle = cmn.fileNameToTitle(fsElem)
                movieDescr = movieTitle
                reg.registerMovie(path, movieTitle, movieDescr, targetDir, createSymlink)
            except Exception as ex:
                cmn.log(f" [ERR] failed to register movie '{fsElem}': {ex}")
        elif os.path.isdir(path) and recursive:
            registerFolder(path, inclPattern, exclPattern, recursive, targetDir, createSymlink)
        else:
            cmn.log(f" [DBG] ignoring '{fsElem}' - neither dir nor (accepted) video file")


def main():
    if cmn.hasSysArg(ARG_HELP) or cmn.hasSysArg(ARG_HELP_LONG):
        printHelp()
        sys.exit(0)
    
    try:
        srcFile = cmn.findSysArgValue(ARG_SRC_FILE, lambda argValue: cmn.isVideoFile(argValue))
        srcDir = cmn.findSysArgValue(ARG_SRC_FOLDER, lambda argValue: os.path.isdir(argValue))
        
        if srcFile != None and srcDir != None:
            raise RuntimeError("only one of the parameters 'source video file' and 'source video folder' may be provided")
        
        if srcFile != None:
            singleMovieMode = True
            
            movieTitle = cmn.findSysArgValue(ARG_MOVIE_NAME, NOOP_VALIDATOR) or cmn.fileNameToTitle(srcFile)
            movieDescr = cmn.findSysArgValue(ARG_MOVIE_DESCRIPTION, NOOP_VALIDATOR) or movieTitle

            cmn.log(f"[INFO] source file: {srcFile}")
            cmn.log(f"[INFO] movie title: {movieTitle}")
            cmn.log(f"[INFO] movie description: {movieDescr}")
        elif srcDir != None:
            singleMovieMode = False
            
            inclGlob = cmn.findSysArgValue(ARG_INCL_GLOB, NOOP_VALIDATOR) or "*"
            exclGlob = cmn.findSysArgValue(ARG_EXCL_GLOB, NOOP_VALIDATOR) or "." # default: a never matching pattern
            recursive = cmn.hasSysArg(ARG_RECURSIVE)
            
            cmn.log(f"[INFO] source root folder: {srcDir}")
            cmn.log(f"[INFO] include GLOB: {inclGlob}")
            cmn.log(f"[INFO] exclude GLOB: {exclGlob}")
            cmn.log(f"[INFO] include subfolders: {recursive}")
        else:
            raise RuntimeError("no valid source video file or folder provided")
            
        targetDir = cmn.findSysArgValue(ARG_MEDIA_DIR, lambda argValue: os.path.isdir(argValue)) or cmn.MEDIA_DIR_PATH
        createSymlink = cmn.hasSysArg(ARG_SYMLINK) or False
        
        cmn.log(f"[INFO] media repository: {targetDir}")
        cmn.log(f"[INFO] symlink movie: {createSymlink}")
        
        if targetDir == None or not os.path.isdir(targetDir):
            raise RuntimeError("no valid media repository provided")
         
        if singleMovieMode:
            reg.registerMovie(srcFile, movieTitle, movieDescr, targetDir, createSymlink)
        else:
            registerFolder(srcDir, cmn.patternFromGlob(inclGlob), cmn.patternFromGlob(exclGlob), recursive, targetDir, createSymlink)
            
        # at last trigger client model refresh
        cmn.log("[INFO] starting client model refresh")
        mdl.refresh(False)
    except Exception as ex:
        cmn.log(f" [ERR] failed to register movie(s): {ex}")
        sys.exit(-1)
    
main()
