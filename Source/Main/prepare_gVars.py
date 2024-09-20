#!/usr/bin/env python3

#===============================================
# updated by ...: Loreto Notarantonio
# Date .........: 03-05-2024 13.36.05
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
import SQLiteDB_Class

import TelegramSendMessage


def setMainVars(logger, prj_name, input_args, type: str=None, search_paths: list=["conf"]):
    global gv



    gv=benedict(keyattr_enabled = True, keyattr_dynamic = False) # copy all input args to gv

    # gv=gVars
    # ----- basic variables
    gv.logger               = logger
    gv.args                 = vars(input_args)
    gv.OpSys: str           = platform.system()
    gv.prj_name: str        = prj_name
    gv.search_paths: list   = search_paths
    gv.date_time: str       = datetime.now().strftime("%Y%m%d_%H%M")
    gv.now: str             = datetime.now().strftime("%d-%m-%Y_%H:%M")
    gv.script_path          = Path(sys.argv[0]).resolve()
    gv.tmp_dir              = f"/tmp/{prj_name}"
    gv.clear_retained       = False
    gv.hostname             = socket.gethostname().split()[0]

    gv.clear_retained                   = False
    gv.envars_dir:              str   = os.environ.get("ln_ENVARS_DIR")
    gv.mqttmonitor_runtime_dir: str   = os.path.expandvars("${ln_RUNTIME_DIR}/mqttMonitor")



    # - set env variables
    os.environ['DATE_TIME'] = gv.date_time
    os.environ['HOST_NAME'] = gv.hostname

    FileLoader.setup(gVars=gv)
    LnUtils.setup(gVars=gv)
    # subprocessLN.setup(gVars=gv)
    dictUtils.setup(gVars=gv)
    SQLiteDB_Class.setup(gVars=gv)

    TelegramSendMessage.setup(gVars=gv)

    gv.telegramMessage = TelegramSendMessage

    return gv

