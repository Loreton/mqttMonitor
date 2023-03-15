#!/usr/bin/python
#
# updated by ...: Loreto Notarantonio
# Date .........: 15-03-2023 18.00.40
#

import  sys; sys.dont_write_bytecode = True
import os

from types import SimpleNamespace




def setup_LnUtils(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    import LnUtils; LnUtils.setup(gVars=gv)



def setup_Tasmota_Telegram_Notification(*, gVars):
    gv=SimpleNamespace()
    gv.logger      = gVars.logger
    if hasattr(gVars, 'prj_name'):          gv.prj_name=gVars.prj_name
    if hasattr(gVars, 'telegramMessage'):   gv.telegramMessage=gVars.telegramMessage

    from Tasmota_Telegram_Notification import setup; setup(gVars=gv)


# def setup_Topic_Process(*, gVars):
#     gv=SimpleNamespace()
#     gv.logger=gVars.logger
#     if hasattr(gVars, 'mqttmonitor_runtime_dir'):   gv.mqttmonitor_runtime_dir=gVars.mqttmonitor_runtime_dir
#     import Topic_Process; Topic_Process.setup(gVars=gv)
#     import Tasmota_Device; Tasmota_Device.setup(gVars=gv)
#     import Shellies_Device; Shellies_Device.setup(gVars=gv)
#     import LnCmnd_Process; LnCmnd_Process.setup(gVars=gv)




def setup_Tasmota_Human_Converter(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    import Tasmota_Human_Converter; Tasmota_Human_Converter.setup(gVars=gv)



def setup_FileLoader(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    import FileLoader; FileLoader.setup(gVars=gv)





def Main(*, gVars):
    import inspect
    this=sys.modules[__name__]
    functions=inspect.getmembers(this, inspect.isfunction)

    for func_name, func_ptr in functions:
        if func_name.startswith('setup_'):
            gVars.logger.notify('initializing module: %s', func_name[6:])
            rc=func_ptr(gVars=gVars)