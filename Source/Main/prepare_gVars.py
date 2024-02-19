#!/usr/bin/python

#===============================================
# updated by ...: Loreto Notarantonio
# Date .........: 19-02-2024 17.20.31
#===============================================

import sys; sys.dont_write_bytecode=True
import os

from    datetime import datetime, timedelta
import platform
import socket
from pathlib import Path
from benedict import benedict


import FileLoader
import LnUtils
import dictUtils
import TelegramSendMessage


def setMainVars(logger, prj_name, input_args, type: str=None):
    global gv
    gv=benedict(keyattr_enabled = True, keyattr_dynamic = False) # copy all input args to gv

    # gv=gVars
    # ----- basic variables
    gv.logger                = logger
    gv.args:            dict = vars(input_args)
    gv.OpSys:           str  = platform.system()
    gv.prj_name:        str  = prj_name
    gv.search_paths:    list = ['conf']
    gv.date_time:       str  = datetime.now().strftime("%Y%m%d_%H%M")
    gv.date_time_2:     str  = datetime.now().strftime("%d-%m-%Y_%H:%M")
    gv.script_path           = Path(sys.argv[0]).resolve()
    gv.tmp_dir:         str  = f"/tmp/{prj_name}"


    gv.clear_retained                   = False
    gv.envars_dir:              str   = os.environ.get("ln_ENVARS_DIR")
    gv.mqttmonitor_runtime_dir: str   = os.path.expandvars("${ln_RUNTIME_DIR}/mqttMonitor")





    # - set env variables
    os.environ['DATE_TIME'] = gv.date_time
    os.environ['HOST_NAME'] = socket.gethostname().split()[0]

    LnUtils.setup(gVars=gv)
    dictUtils.setup(gVars=gv)
    FileLoader.setup(gVars=gv)
    TelegramSendMessage.setup(gVars=gv)

    gv.telegramMessage = TelegramSendMessage

    return gv


# def setExtraVars():
#     gv.read_file_content   = FileLoader.read_file_content
#     gv.common_include_file = FileLoader.common_include_file


