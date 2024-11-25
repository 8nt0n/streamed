import streamed_tools_common as cmn

ARG_SRC_FILE = '-s'
ARG_MOVIE_TITLE = '-t'
ARG_MOVIE_DESCR = '-d'

NOOP_VALIDATOR = lambda argValue: True

def main():
    srcFile = cmn.findSysArgValue(ARG_SRC_FILE, lambda argValue: cmn.isFile(argValue))
    movieTitle = cmn.findSysArgValue(ARG_MOVIE_TITLE, NOOP_VALIDATOR)
    movieDescr = cmn.findSysArgValue(ARG_MOVIE_DESCR, NOOP_VALIDATOR)
    
    
    cmn.log(f'[INFO] source file: {srcFile}')
    cmn.log(f'[INFO] movie title: {movieTitle}')
    cmn.log(f'[INFO] movie description: {movieDescr}')
    
    
main()