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

    args=ParseInput()
    logger=setColoredLogger(logger_name='mqtt_monitor',
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_file=args.logging_file,
                            threads=False)
    testLogger(logger)
    LnDict.setLogger(mylogger=logger)
    os.environ["ln_RUNTIME_DIR"]="/home/loreto/ln_runtime"

    gVars={
        "systemd": args.systemd,
        "logger": logger,
        "topic_list": args.topics,
        "clear_retained": False,
        "monitor": args.monitor,
        "pid_file": args.pid_file,
    }
    savePidFile(gVars['pid_file'])

    # mqttClientMonitor.run(topic_list=args.topics, my_logger=logger, systemd=args.systemd)
    mqttClientMonitor.run(gVars)
