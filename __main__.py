#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os, glob
from types import SimpleNamespace



import Source
import mqttClientMonitor
import LoretoDict

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
from savePidFile import savePidFile



if __name__ == '__main__':
    prj_name='mqttMonitor'
    args=ParseInput()
    logger=setColoredLogger(logger_name=prj_name.lower(),
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False)
    testLogger(logger)




    user=os.environ.get('USER')
    # mqttmonitor_runtime_dir=f"/home/{user}/ln_runtime/mqtt_monitor"
    mqttmonitor_runtime_dir=os.path.expandvars("${ln_RUNTIME_DIR}/mqtt_monitor")


    if args.clean_files:
        files = glob.glob(f"{mqttmonitor_runtime_dir}/*.json")
        for f in files:
            os.remove(f)
        files = glob.glob(f"{mqttmonitor_runtime_dir}/*yaml")
        for f in files:
            os.remove(f)


    gv=SimpleNamespace()
    gv.clear_retained          = False
    gv.logger                  = logger
    gv.prj_name                = prj_name
    gv.just_monitor            = args.monitor
    gv.pid_file                = args.pid_file
    gv.systemd                 = args.systemd
    gv.tgGroupName             = args.telegram_group_name
    gv.topic_list              = args.topics
    gv.mqttmonitor_runtime_dir = mqttmonitor_runtime_dir
    gv.envars_dir              = os.environ.get("ln_ENVARS_DIR")
    savePidFile(gv.pid_file)

    import InitializeModules; InitializeModules.Main(gVars=gv)

    # mqttClientMonitor.run(topic_list=args.topics, my_logger=logger, systemd=args.systemd)
    mqttClientMonitor.run(gVars=gv)
