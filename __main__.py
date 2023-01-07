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

    import InitializeModules; InitializeModules.Main(gVars=gv)

    savePidFile(gv.pid_file)
    mqttClientMonitor.run(gVars=gv)
