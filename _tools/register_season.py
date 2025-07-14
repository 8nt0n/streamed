import sys
import traceback

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl
import lib_register_media_collection as rmc

USAGE_EXAMPLES = (
    "# register (copy) all episodes of the first season of a series:\n"
    + f"python {sys.argv[0]} \\ \n"
    + f" {rmc.ARG_SRC_FOLDER} /home/me/videos/rick_morty_season01/ \\ \n"
    + f" {rmc.ARG_TARGET_FOLDER} rick_and_morty \\ \n"
    + f" {rmc.ARG_COLLECTION_NAME} \"Rick and Morty\" \\ \n"
    + f" {rmc.ARG_COLLECTION_DESCRIPTION} \"\\\"Rick and Morty\\\" is an American animated science fiction sitcom created by Justin Roiland and Dan Harmon.\"\n"
    + "# register (symlink) all episodes of season 8 of an existing (already registered) series:\n"
    + f"python {sys.argv[0]}"
    + f" {rmc.ARG_SRC_FOLDER} /home/me/videos/rick_morty_season08/"
    + f" {rmc.ARG_TARGET_FOLDER} rick_and_morty"
    + f" {rmc.ARG_SUBCOLLECTION_NUMBER} 8"
    + f" {rmc.ARG_SYMLINK}\n"
)

def main():
    try:
        # check command line arguments and do the registration
        rmc.checkAndRegister(cmn.MEDIA_TYPE_SERIES, USAGE_EXAMPLES)
                        
        # at last trigger client model refresh
        cmn.log("[INFO] starting client model refresh")
        mdl.refresh(False)
    except Exception as ex:    
        cmn.log(f" [ERR] failed to register episodes: {ex}")
        print(traceback.format_exc())
        sys.exit(-1)
    
main()
