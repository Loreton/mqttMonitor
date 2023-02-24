#!/usr/bin/python
#
# updated by ...: Loreto Notarantonio
# Date .........: 24-02-2023 13.29.21
#

import  sys; sys.dont_write_bytecode = True
import os

from types import SimpleNamespace




def setup_LnUtils(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    import LnUtils; LnUtils.setup(gVars=gv)



def setup_Telegram_Notification(*, gVars):
    gv=SimpleNamespace()
    gv.logger      = gVars.logger
    gv.prj_name    = gVars.prj_name
    gv.telegramMessage    = gVars.telegramMessage

    from Telegram_Notification import setup; setup(gVars=gv)


def setup_Topic_Process(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    gv.mqttmonitor_runtime_dir = os.path.expandvars("${ln_RUNTIME_DIR}/mqtt_monitor")
    import Topic_Process; Topic_Process.setup(gVars=gv)



def setup_Tasmota_Human_Converter(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    import Tasmota_Human_Converter; Tasmota_Human_Converter.setup(gVars=gv)




def Main(*, gVars):
    import inspect
    this=sys.modules[__name__]
    functions=inspect.getmembers(this, inspect.isfunction)

    for func_name, func_ptr in functions:
        if func_name.startswith('setup_'):
            gVars.logger.notify('initializing module: %s', func_name[6:])
            rc=func_ptr(gVars=gVars)