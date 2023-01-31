#!/usr/bin/python
#
# updated by ...: Loreto Notarantonio
# Date .........: 31-01-2023 10.23.04
#

import  sys; sys.dont_write_bytecode = True
import os

from types import SimpleNamespace


def setup_Telegram_Notification(*, gVars):
    gv=SimpleNamespace()
    gv.logger      = gVars.logger
    gv.prj_name    = gVars.prj_name

    from Telegram_Notification import setup; setup(gVars=gv)


# def setup_LoadConfigFile(*, gVars):
#     gv=SimpleNamespace()
#     gv.logger=gVars.logger
#     import LoadConfigFile; LoadConfigFile.setup(gVars=gv)


def setup_SendTelegramMessage(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    gv.telegramData=gVars.telegramData
    import SendTelegramMessage; SendTelegramMessage.setup(gVars=gv)


def setup_Topic_Process(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    gv.mqttmonitor_runtime_dir = os.path.expandvars("${ln_RUNTIME_DIR}/mqtt_monitor")
    import Topic_Process; Topic_Process.setup(gVars=gv)



def setup_LnUtils(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    import LnUtils; LnUtils.setup(gVars=gv)




def Main(*, gVars):
    import inspect
    this=sys.modules[__name__]
    functions=inspect.getmembers(this, inspect.isfunction)

    for func_name, func_ptr in functions:
        if func_name.startswith('setup_'):
            gVars.logger.notify('initializing module: %s', func_name[6:])
            rc=func_ptr(gVars=gVars)