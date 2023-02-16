#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os, glob
from types import SimpleNamespace
from benedict import benedict



import Source
import mqttClientMonitor

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
from savePidFile import savePidFile
# from LoadConfigFile import readYamlFile
import FileLoader
from TelegramSendMessage_Class import TelegramSendMessage_Class


__ln_version__="mqttMonitor Version: V2023-02-16_180544"

if __name__ == '__main__':
    prj_name='mqttMonitor'
    args=ParseInput(__ln_version__)
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False)
    gv=SimpleNamespace()
    gv.logger                  = logger

    logger.warning(__ln_version__)



    # config=readYamlFile(filename=f'mqttMonitor.yaml', logger=logger, search_paths=['conf'], resolve_includes=True, to_benedict=True, exit_on_error=True)
    # read all configuration data
    config=FileLoader.read_yaml(filename='mqttMonitor.yaml', search_paths=['conf'])
    if not config:
        logger.error('configuration data NOT found')
        sys.exit(1)
    config=benedict(config)

    gv.telegramMessage=TelegramSendMessage_Class(telegram_group_data_file="telegramGroups.lnk.yaml", logger=logger)

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
