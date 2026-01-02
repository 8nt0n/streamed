import glob
import os
import shutil
import sys
import traceback

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl
import lib_register as reg

ARG_SRC_FOLDER = "-s" # "-f"
ARG_TARGET_FOLDER = "-t" # "-s"
ARG_SUBCOLLECTION_NUMBER = "-c" # "-n"
ARG_COLLECTION_NAME = "-n" # "-t"
ARG_COLLECTION_DESCRIPTION = "-d"
ARG_RECURSIVE = "-r"
ARG_MEDIA_DIR = "-m"
ARG_SYMLINK = "-l"
ARG_INCL_GLOB = "-i"
ARG_EXCL_GLOB = "-e"

NOOP_VALIDATOR = lambda argValue: True


def printHelp(usageExamples):
    print(
        "Usage:\n"
        + f"python {sys.argv[0]}"
        + f" {ARG_SRC_FOLDER} <source media folder>"
        + f" {ARG_TARGET_FOLDER} <target folder name>"
        + f" [{ARG_SUBCOLLECTION_NUMBER} <(sub)collection number>]"
        + f" [{ARG_COLLECTION_NAME} <collection name>]"
        + f" [{ARG_COLLECTION_DESCRIPTION} <collection description>]"
        + f" [{ARG_MEDIA_DIR} <media repository>]"
        + f" [{ARG_SYMLINK}]"
        + f" [{ARG_INCL_GLOB} <include files glob>]"
        + f" [{ARG_EXCL_GLOB} <exclude files glob>]"
        + f" [{cmn.ARG_VERBOSE}]\n"

        + "This script adds a new collection of media files( e.g. episodes of a series or a music album) to the media repository.\n\n"
        + f"Arguments:\n"
        + f"{ARG_SRC_FOLDER}           path to the folder containing the media files of the collection to register (mandatory)\n"
        + f"{ARG_TARGET_FOLDER}           name of the target folder in the media repository hosting this collection\n"
        + f"{ARG_SUBCOLLECTION_NUMBER}           number of the (sub) collection to register, defaults to 1 (overwrites existing media files)\n"
        + f"{ARG_MEDIA_DIR}           path to the target media repository containing your streamable media, defaults to {cmn.MEDIA_DIR_PATH}\n"
        + f"{ARG_COLLECTION_NAME}           the collection's name when adding a sub-collection of a new collection to the media repository (will be extracted from the collection's target folder if not present)\n"
        + f"{ARG_COLLECTION_DESCRIPTION}           the collection's description when adding a sub-collection of a new collection to the media repository (defaults to the collection's name)\n"
        + f"{ARG_INCL_GLOB}           include only media files matching the provided GLOB (ignoring case) when processing the source media folder\n"
        + f"{ARG_EXCL_GLOB}           exclude all media files matching the provided GLOB (ignoring case) when processing the source media folder\n"
        + f"{ARG_SYMLINK}           create symlinks to the source media files instead of copying them to the media repository (must be supported by the operating system) - use with caution!\n"
        + f"{cmn.ARG_VERBOSE}           enables a more verbose logging\n"
        + f"{cmn.ARG_HELP}, {cmn.ARG_HELP_LONG}   print usage information and exit\n"
    )
    
    print("Usage examples:\n" + usageExamples)
    

def checkAndRegister(mediaType, usageExamples):
    if cmn.hasSysArg(cmn.ARG_HELP) or cmn.hasSysArg(cmn.ARG_HELP_LONG):
        printHelp(usageExamples)
        sys.exit(0)
    
    srcDir = cmn.findSysArgValue(ARG_SRC_FOLDER, lambda argValue: os.path.isdir(argValue))        
    if srcDir == None:
        raise RuntimeError("no valid source media folder provided")
    
    targetDir = cmn.findSysArgValue(ARG_TARGET_FOLDER, lambda argValue: not os.path.isfile(argValue))
    if targetDir == None:
        raise RuntimeError("no valid target media folder provided")
    
    collectionNum = cmn.findSysArgValue(ARG_SUBCOLLECTION_NUMBER, lambda argValue: argValue != None and argValue.isdigit()) or "1"
    inclGlob = cmn.findSysArgValue(ARG_INCL_GLOB, NOOP_VALIDATOR) or "*"
    exclGlob = cmn.findSysArgValue(ARG_EXCL_GLOB, NOOP_VALIDATOR) or "." # default: a never matching pattern
    collectionName = cmn.findSysArgValue(ARG_COLLECTION_NAME, NOOP_VALIDATOR) or cmn.fileNameToTitle(targetDir)
    collectionDescr = cmn.findSysArgValue(ARG_COLLECTION_DESCRIPTION, NOOP_VALIDATOR) or collectionName
    mediaRepoDir = cmn.findSysArgValue(ARG_MEDIA_DIR, lambda argValue: os.path.isdir(argValue)) or cmn.MEDIA_DIR_PATH
    createSymlink = cmn.hasSysArg(ARG_SYMLINK) or False
    
    cmn.log(f"[INFO] source root folder: {srcDir}")
    cmn.log(f"[INFO] target folder name: {targetDir}")
    cmn.log(f"[INFO] (sub) collection number: {collectionNum}")
    cmn.log(f"[INFO] include GLOB: {inclGlob}")
    cmn.log(f"[INFO] exclude GLOB: {exclGlob}")
    cmn.log(f"[INFO] collection name: {collectionName}")
    cmn.log(f"[INFO] collection description: {collectionDescr}")
    cmn.log(f"[INFO] media repository: {mediaRepoDir}")
    cmn.log(f"[INFO] symlink episodes: {createSymlink}")
    
    if mediaRepoDir == None or not os.path.isdir(mediaRepoDir):
        raise RuntimeError("no valid media repository provided")

    register(
        mediaType,
        srcDir,
        targetDir,
        collectionNum,
        cmn.patternFromGlob(inclGlob),
        cmn.patternFromGlob(exclGlob),
        mediaRepoDir,
        createSymlink,
        collectionName,
        collectionDescr            
    )


def register(mediaType, srcDir, targetDir, collectionNum, inclPattern, exclPattern, mediaRepoDir, createSymlink, collectionName, collectionDescr):
    targetPath = os.path.join(mediaRepoDir, mediaType, targetDir, collectionNum) # TODO: use constant               
    cmn.makeDirs(targetPath)
        
    collectionBseDir = cmn.parentDirOf(targetPath)
    cmn.log(f" [DBG] collection base dir: {collectionBseDir}")
    
    metaFolder = os.path.join(collectionBseDir, "meta") # TODO: use constant
    cmn.makeDirs(metaFolder)

    # create description text file in the 'meta' subfolder
    descrFilePath = os.path.join(metaFolder, "description.txt") # TODO: use constant
    if not os.path.isfile(descrFilePath):
        collectionDescr = collectionDescr or collectionName
        try:
            cmn.writeTextFile(descrFilePath, collectionDescr)
            cmn.log(f" [DBG] description written to {descrFilePath}")
        except Exception as ex:
            cmn.log(f"[WARN] failed to write the description text file {descrFilePath}: {ex}")     
            raise ex
        
    titleFilePath = os.path.join(metaFolder, "title.txt") # TODO: use constant
    if not os.path.isfile(titleFilePath):
        try:
            cmn.writeTextFile(titleFilePath, collectionName)        
            cmn.log(f" [DBG] title written to {titleFilePath}")
        except Exception as ex:
            cmn.log(f"[WARN] failed to write the title text file {titleFilePath}: {ex}")     
            raise ex
    
    if mediaType == cmn.MEDIA_TYPE_AUDIOS:
        mediaTypeCheck = lambda srcPathArg: cmn.isAudioFile(srcPathArg)
    else:
        mediaTypeCheck = lambda srcPathArg: cmn.isVideoFile(srcPathArg)

    num = 0
    orderedFiles = cmn.orderedFileList(srcDir)
    for fsElem in orderedFiles:
        srcPath = os.path.join(srcDir, fsElem)
        if mediaTypeCheck(srcPath) and inclPattern.fullmatch(fsElem) != None and exclPattern.fullmatch(fsElem) == None:
            num = num + 1
            try:
                reg.registerCollectionFile(srcPath, targetPath, mediaRepoDir, num, createSymlink)
            except Exception as ex:
                cmn.log(f" [ERR] failed to register media collection file '{fsElem}': {ex}")
        else:
            cmn.log(f" [DBG] ignoring '{fsElem}' - not a (accepted) media file")
