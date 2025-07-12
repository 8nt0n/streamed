import os
import shutil
import sys

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl

# TODO: currently movieTitle is only used movie dir generation and gets lost after this - consider storing it to have it
#       available during client model refresh 
def registerMovie(srcFile, movieTitle, movieDescr, targetDir, createSymlink):
    if srcFile == None:
        raise RuntimeError("no valid video file provided")

    if targetDir == None or not os.path.isdir(targetDir):
        raise RuntimeError("no valid media repository provided")

    # create the movie dir and the 'meta' subfolder
    movieFolder = os.path.join(targetDir, cmn.MEDIA_TYPE_MOVIES, cmn.titleToFileName(movieTitle))
    if os.path.isdir(movieFolder):
        raise RuntimeError(f"movie directory '{movieFolder}' already exists")
    
    metaFolder = os.path.join(movieFolder, "meta") # TODO: use constant
    os.makedirs(metaFolder)
    if os.path.isdir(metaFolder):
        cmn.log(f" [DBG] directories created: {metaFolder}")
    else:
        raise RuntimeError(f"failed to create directory '{metaFolder}'")
    
    # copy (or link) video file
    if createSymlink: # problematic under Windows
        symlinkPath = os.path.join(movieFolder, os.path.basename(srcFile))
        try:
            os.symlink(srcFile, symlinkPath)
            cmn.log(f" [DBG] symlink to {srcFile} created: {symlinkPath}")
        except Exception as ex:
            cmn.log(f" [ERR] failed to symlink {srcFile} to {symlinkPath}: {ex}")
            raise ex
    else:
        shutil.copy2(srcFile, movieFolder)  # use shutil.copy2() to preserve timestamp
        cmn.log(f" [DBG] {srcFile} copied to {movieFolder}")
    
    # create description text file in the 'meta' subfolder
    descrFilePath = os.path.join(metaFolder, "description.txt") # TODO: use constant
    descrContent = cmn.readTextFile(movieDescr) if os.path.isfile(movieDescr) else movieDescr
    try:
        cmn.writeTextFile(descrFilePath, descrContent)        
        cmn.log(f" [DBG] description written to {descrFilePath}")
    except Exception as ex:
        cmn.log(f"[WARN] failed to write the description text file {descrFilePath}: {ex}")     
        raise ex
        

def registerEpisode(srcFile, targetSeasonDir, mediaRepoDir, episodeNum, createSymlink):
    cmn.log(f"[INFO] registering episode '{srcFile}' (target: '{targetSeasonDir}')")
    
    if srcFile == None:
        raise RuntimeError("no valid video file provided")

    # copy (or link) video file
    targetPath = os.path.join(targetSeasonDir, str(episodeNum) + cmn.fileExtensionOf(srcFile))
    if createSymlink: # problematic under Windows
        symlinkPath = targetPath
        try:
            os.symlink(srcFile, symlinkPath)
            cmn.log(f" [DBG] symlink to {srcFile} created: {symlinkPath}")
        except Exception as ex:
            cmn.log(f" [ERR] failed to symlink {srcFile} to {symlinkPath}: {ex}")
            raise ex
    else:
        shutil.copy2(srcFile, targetPath)  # use shutil.copy2() to preserve timestamp
        cmn.log(f" [DBG] {srcFile} copied to {targetPath}")


def registerAlbumTrack(srcFile, targetSeasonDir, mediaRepoDir, episodeNum, createSymlink):
    cmn.log(f"[INFO] registering album track '{srcFile}' (target: '{targetSeasonDir}')")
    
    if srcFile == None:
        raise RuntimeError("no valid video file provided")

    # copy (or link) video file
    targetPath = os.path.join(targetSeasonDir, str(episodeNum) + cmn.fileExtensionOf(srcFile))
    if createSymlink: # problematic under Windows
        symlinkPath = targetPath
        try:
            os.symlink(srcFile, symlinkPath)
            cmn.log(f" [DBG] symlink to {srcFile} created: {symlinkPath}")
        except Exception as ex:
            cmn.log(f" [ERR] failed to symlink {srcFile} to {symlinkPath}: {ex}")
            raise ex
    else:
        shutil.copy2(srcFile, targetPath)  # use shutil.copy2() to preserve timestamp
        cmn.log(f" [DBG] {srcFile} copied to {targetPath}")
