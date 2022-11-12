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


if __name__ == '__main__':
    args=ParseInput()
    logger=setColoredLogger(logger_name='mqtt_monitor', console_logger_level=args.console_logger_level, file_logger_level='debug', logging_file='/tmp/mqttmonitor.log')
    testLogger(logger)

    mqttClientMonitor.run(topic_list=args.topics, my_logger=logger)
