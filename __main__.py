#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os, glob
from types import SimpleNamespace



import Source
import mqttClientMonitor

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
from savePidFile import savePidFile
from LoadConfigFile import readYamlFile


__ln_version__="mqttMonitor Version: V2023-02-01_095010"

if __name__ == '__main__':
    prj_name='mqttMonitor'
    args=ParseInput()
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False)
    logger.warning(__ln_version__)
    # testLogger(logger)



    config=readYamlFile(filename=f'conf/mqttMonitor.yaml', search_paths=['conf'], resolve_includes=True, to_benedict=True)
    if not config:
        logger.error('configuration data NOT found')
        sys.exit(1)

    gv=SimpleNamespace()
    gv.logger                  = logger
    gv.prj_name                = prj_name
    gv.clear_retained          = False
    gv.just_monitor            = args.monitor
    gv.pid_file                = args.pid_file
    gv.systemd                 = args.systemd
    gv.tgGroupName             = args.telegram_group_name
    gv.topic_list              = args.topics
    gv.telegramData            = config['telegram']
    gv.broker                  = config['broker']

    import InitializeModules;
    InitializeModules.Main(gVars=gv)

    savePidFile(gv.pid_file)
    mqttClientMonitor.run(gVars=gv)
