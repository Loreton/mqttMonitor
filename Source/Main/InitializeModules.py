#!/usr/bin/python
#
# updated by ...: Loreto Notarantonio
# Date .........: 17-12-2022 08.09.37
#

import  sys; sys.dont_write_bytecode = True
import os

from types import SimpleNamespace


def setup_Telegram_Notification(*, gVars):
    gv=SimpleNamespace()
    gv.logger      = gVars.logger
    gv.prj_name    = gVars.prj_name

    from Telegram_Notification import setup; setup(gVars=gv)


def setup_LoadYamlFile_Class(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    gv.envars_dir              = os.path.expandvars("${ln_ENVARS_DIR}")
    gv.mqttmonitor_runtime_dir = os.path.expandvars("${ln_RUNTIME_DIR}/mqtt_monitor")
    gv.brokers_file            = os.path.expandvars("${ln_ENVARS_DIR}/yaml/Mqtt_Brokers.yaml")
    gv.telegram_groups_file    = os.path.expandvars("${ln_ENVARS_DIR}/yaml/telegramGroups.yaml")
    gv.mariadb_file            = os.path.expandvars("${ln_ENVARS_DIR}/yaml/mariadb.yaml")

    import LoadYamlFile_Class; LoadYamlFile_Class.setup(gVars=gv)




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
    setup_Telegram_Notification(gVars=gVars)
    setup_LnUtils(gVars=gVars)
    setup_LoadYamlFile_Class(gVars=gVars)
    setup_Topic_Process(gVars=gVars)

