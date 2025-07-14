import sys
import traceback

import lib_streamed_tools_common as cmn
import lib_generate_client_model as mdl
import lib_register_media_collection as rmc

USAGE_EXAMPLES = (
    "# register (copy) all tracks of a music album:\n"
    + f"python {sys.argv[0]}"
    + f" {rmc.ARG_SRC_FOLDER} /home/me/audio/ramones-brain_drain/"
    + f" {rmc.ARG_TARGET_FOLDER} the_ramones-brain_drain\n"
    + "# register (copy) all tracks of the second record of a double album (with the first record already registered under 'the_ramones-its_alive'):\n"
    + f"python {sys.argv[0]}"
    + f" {rmc.ARG_SRC_FOLDER} /home/me/audio/ramones-its_alive/"
    + f" {rmc.ARG_TARGET_FOLDER} the_ramones-its_alive"
    + f" {rmc.ARG_SUBCOLLECTION_NUMBER} 2"
)

def main():
    try:
        # check command line arguments and do the registration
        rmc.checkAndRegister(cmn.MEDIA_TYPE_AUDIOS, USAGE_EXAMPLES)
            
        # at last trigger client model refresh
        cmn.log("[INFO] starting client model refresh")
        mdl.refresh(False)
    except Exception as ex:    
        cmn.log(f" [ERR] failed to register episodes: {ex}")
        print(traceback.format_exc())
        sys.exit(-1)
    
main()
