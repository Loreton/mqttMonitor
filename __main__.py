#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os

import Source
from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
import mqttClientMonitor
from savePidFile import savePidFile
import LnDict



if __name__ == '__main__':
    prj_name='mqttmonitor'
    args=ParseInput()
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False)
    testLogger(logger)
    LnDict.setLogger(mylogger=logger)
    user=os.environ.get('USER')
    os.environ["ln_RUNTIME_DIR"]=f"/home/{user}/ln_runtime"

    gVars={
        "systemd": args.systemd,
        "logger": logger,
        "topic_list": args.topics,
        "clear_retained": False,
        "monitor": args.monitor,
        "pid_file": args.pid_file,
        "tgGroupName": args.telegram_group_name,
    }
    savePidFile(gVars['pid_file'])

    # mqttClientMonitor.run(topic_list=args.topics, my_logger=logger, systemd=args.systemd)
    mqttClientMonitor.run(gVars)
