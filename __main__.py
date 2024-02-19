#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os

from types import SimpleNamespace
from benedict import benedict
from datetime import datetime, timedelta
import platform


## Project modules
os.environ['Loader_modules']="csv ini yaml json"
import Source
import prepare_gVars
import LnUtils
import FileLoader
import mqttClientMonitor

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
from savePidFile import savePidFile

from devicesDB import devicesDB_Class



def setVars(type: str=None):
    global gv
    if type=="01":
        # ----- basic variables
        gv=benedict(**vars(args), keyattr_enabled=True, keyattr_dynamic=False) # copy all input args to gv
        gv.logger               = logger
        gv.OpSys: str           = platform.system()
        gv.prj_name: str        = prj_name
        gv.search_paths: list   = ['conf']
        gv.date_time: str       = datetime.now().strftime("%Y%m%d_%H%M")
        gv.tmp_dir              = f"/tmp/{prj_name}"
        os.environ['DATE_TIME'] = gv.date_time

        # ----- modules initialization
        LnUtils.setup(gVars=gv)
        FileLoader.setup(gVars=gv)
        TelegramSendMessage.setup(gVars=gv)



    else:
        gv.clear_retained                   = False
        gv.args                             = args
        gv.mqttmonitor_runtime_dir: str     = os.path.expandvars(f"$ln_RUNTIME_DIR/{prj_name}")
        gv.envars_dir: str                  = os.environ.get("ln_ENVARS_DIR")
        gv.config: dict                     = config
        gv.obj_devicesDB: devicesDB_Class   = obj_devicesDB
        gv.broker                           = obj_devicesDB.getBroker()
        gv.telegramMessage                  = TelegramSendMessage

    return gv


#######################################################
#
#######################################################
if __name__ == '__main__':
    prj_name='mqttMonitor'
    __ln_version__=f"{prj_name} version: V2024-02-19_172401"
    args=ParseInput(__ln_version__)

    # ---- Loggging
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False,
                            create_logging_dir=True)



    logger.info('------- Starting -----------')
    logger.warning(__ln_version__)

    # ----- basic variables
    gv=prepare_gVars.setMainVars(logger=logger, input_args=args, prj_name=prj_name)

    ### ===============================================
    ### -   Load configuration data
    ### ===============================================
    config_file=f"{prj_name}_config.yaml"
    if not (config:=FileLoader.loadConfigurationData(config_file=config_file, tmp_dir=gv.tmp_dir, gVars=gv, return_resolved=False)):
        logger.error("Configuration data error")
        sys.exit(1)

    ### extract devices e lo passa al devicesDB
    only_devices=config.pop("devices")
    gv.obj_devicesDB=devicesDB_Class(db_data=only_devices, error_on_duplicate=True, logger=logger)

    config.resolveDictCrossReferences()
    config.toYaml(filepath=f"/tmp/resolved_config.yaml", replace=True)
    gv.config: dict = config
    gv.broker: dict = gv.obj_devicesDB.getBroker()

    ### ===============================================


    # savePidFile(args.pid_file)
    mqttClientMonitor.run(gVars=gv)
