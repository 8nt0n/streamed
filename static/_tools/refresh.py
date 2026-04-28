import sys

import lib_generate_client_model as mdl
import lib_streamed_tools_common as cmn

ARG_HELP = "-h"
ARG_HELP_LONG = "--help"
ARG_FORCE = "-f"

def printHelp():
    print(
        "Usage:\n"
        + f"python {sys.argv[0]}"
        + f" [{ARG_FORCE}] [{cmn.ARG_VERBOSE}]\n"

        + "This script refreshes the client model.\n\n"
        + f"Arguments:\n"
        + f"{ARG_FORCE}           forces the (re-)creation of thumbnails\n"
        + f"{cmn.ARG_VERBOSE}           enables a more verbose logging\n"
        + f"{ARG_HELP}, {ARG_HELP_LONG}   print usage information and exit\n"
    )


def main():
    if cmn.hasSysArg(ARG_HELP) or cmn.hasSysArg(ARG_HELP_LONG):
        printHelp()
        sys.exit(0)
        
    mdl.refresh(cmn.hasSysArg(ARG_FORCE))
    
    
main()