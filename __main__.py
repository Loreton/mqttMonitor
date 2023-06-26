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

import FileLoader
from TelegramSendMessage_Class import TelegramSendMessage_Class


__ln_version__="mqttMonitor Version: V2023-06-26_122415"

if __name__ == '__main__':
    prj_name='mqttMonitor'
    args=ParseInput(__ln_version__)
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False,
                            create_logging_dir=True)

    gv=SimpleNamespace()
    gv.logger = logger

    logger.warning(__ln_version__)

    import InitializeModules; InitializeModules.Main(gVars=gv) ### inizialmente solo il logger


    # read all configuration data
    config=FileLoader.load_yaml(filename='mqttMonitor.yaml', search_paths=['conf'])
    if not config:
        logger.error('configuration data NOT found')
        sys.exit(1)
    gv.config=benedict(config)

    FileLoader.setVariables(gv.config['system_variables'])
    gv.telegramMessage=TelegramSendMessage_Class(telegram_group_data=gv.config['telegram'], logger=logger)



    gv.prj_name                = prj_name
    gv.clear_retained          = False
    gv.args                    = args
    gv.telegramData            = gv.config['telegram']
    gv.broker                  = gv.config['broker']
    gv.mqttmonitor_runtime_dir = os.path.expandvars("${ln_RUNTIME_DIR}/mqttMonitor")

    InitializeModules.Main(gVars=gv) ### initializing per altre variabili.

    savePidFile(gv.args.pid_file)
    mqttClientMonitor.run(gVars=gv)
