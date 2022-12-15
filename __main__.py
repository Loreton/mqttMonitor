#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os, glob
from types import SimpleNamespace



import Source
import mqttClientMonitor
# import LoretoDict

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
from savePidFile import savePidFile
from LoadYamlFile_Class import LoadYamlFile_Class


if __name__ == '__main__':
    prj_name='mqttMonitor'
    args=ParseInput()
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=True)
    testLogger(logger)


    gv=SimpleNamespace()
    gv.logger                  = logger
    gv.prj_name                = prj_name

    gv.clear_retained          = False
    gv.just_monitor            = args.monitor
    gv.pid_file                = args.pid_file
    gv.systemd                 = args.systemd
    gv.tgGroupName             = args.telegram_group_name
    gv.topic_list              = args.topics

    gv.envars_dir              = os.path.expandvars("${ln_ENVARS_DIR}")
    gv.mqttmonitor_runtime_dir = os.path.expandvars("${ln_RUNTIME_DIR}/mqtt_monitor")
    gv.brokers_file            = os.path.expandvars("${ln_ENVARS_DIR}/yaml/Mqtt_Brokers.yaml")
    gv.telegram_groups_file    = os.path.expandvars("${ln_ENVARS_DIR}/yaml/telegramGroups.yaml")
    gv.mariadb_file            = os.path.expandvars("${ln_ENVARS_DIR}/yaml/mariadb.yaml")

    import InitializeModules; InitializeModules.Main(gVars=gv)

    if args.clean_files:
        files = glob.glob(f"{gv.mqttmonitor_runtime_dir}/*.json")
        for f in files:
            os.remove(f)
        files = glob.glob(f"{gv.mqttmonitor_runtime_dir}/*yaml")
        for f in files:
            os.remove(f)

    # gv.mqttmonitor_runtime_dir = mqttmonitor_runtime_dir
    # gv.envars_dir              = os.environ.get("ln_ENVARS_DIR")
    savePidFile(gv.pid_file)


    # mqttClientMonitor.run(topic_list=args.topics, my_logger=logger, systemd=args.systemd)
    mqttClientMonitor.run(gVars=gv)
