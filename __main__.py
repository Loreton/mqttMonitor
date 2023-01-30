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
from LoadConfigFile import readYamlFile


if __name__ == '__main__':
    prj_name='mqttMonitor'
    args=ParseInput()
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False)
    # testLogger(logger)

    gv=SimpleNamespace()


    config=readYamlFile(filename=f'conf/{prj_name}.yaml', search_paths=['conf'], resolve_includes=True, to_benedict=True)
    # print(config.to_yaml())

    gv.logger                  = logger
    gv.prj_name                = prj_name
    gv.clear_retained          = False
    gv.just_monitor            = args.monitor
    gv.pid_file                = args.pid_file
    gv.systemd                 = args.systemd
    gv.tgGroupName             = args.telegram_group_name
    gv.topic_list              = args.topics
    gv.telegramData            = config['telegram']
    gv.broker                   = config['broker']

    import InitializeModules;
    InitializeModules.Main(gVars=gv)

    savePidFile(gv.pid_file)
    mqttClientMonitor.run(gVars=gv)
