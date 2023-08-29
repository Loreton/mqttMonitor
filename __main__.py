#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os, glob

from types import SimpleNamespace
from benedict import benedict
from datetime import datetime, timedelta
import platform



import Source
import mqttClientMonitor

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
from savePidFile import savePidFile

import FileLoader
import LnUtils
from    devicesDB import devicesDB_Class

from TelegramSendMessage_Class import TelegramSendMessage_Class


#######################################################
#
#######################################################
def loadConfigurationData(gVars: dict):
    LnUtils.setup(gVars)
    FileLoader.setup(gVars)


    config: dict = FileLoader.load_yaml(filename=f'{prj_name}_config.yaml', to_dict="benedict", remove_templates=True)
    """Load configuration data"""

    LnUtils.writeFile(filepath=f"/tmp/{prj_name}/{prj_name}_unresolved_config.yaml", data=config, replace=True)
    """save unresolved configuration data"""

    FileLoader.resolve_my_references(d=config["devices_data"])
    """resolve internal cross references"""

    FileLoader.resolve_my_references(d=config)
    """resolve internal cross references"""

    LnUtils.writeFile(filepath=f"/tmp/{prj_name}/{prj_name}_full_config.yaml", data=config, replace=True)
    """save full configuration data"""


    system_variables=config.pop("system_variables")
    FileLoader.setVariables(data=system_variables)
    """Setting environment variables"""

    return config



#######################################################
#
#######################################################
if __name__ == '__main__':
    prj_name='mqttMonitor'
    __ln_version__=f"{prj_name} version: V2023-08-29_162659"
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

    date_time=datetime.now().strftime("%Y%m%d_%H%M")

    gv=benedict(**vars(args), keyattr_enabled=True, keyattr_dynamic=False) # copy all input args to gv
    gv.logger             = logger
    gv.OpSys: str         = platform.system()
    gv.prj_name: str      = prj_name
    gv.search_paths: list = ['conf']
    gv.date_time: str     = datetime.now().strftime("%Y%m%d_%H%M")

    os.environ['DATE_TIME']=gv.date_time
    config=loadConfigurationData(gVars=gv)

    devices_data=config.pop("devices_data")
    devicesDB=devicesDB_Class(db_data=devices_data, error_on_duplicate=True, save_on_file=True, logger=logger, prj_name=prj_name)
    """instantiate deviceaDB class (crea gli indici per alcuni attributi) """




    gv.clear_retained               = False
    gv.args                         = args
    gv.mqttmonitor_runtime_dir: str = os.path.expandvars("${ln_RUNTIME_DIR}/mqttMonitor")
    gv.envars_dir: str              = os.environ.get("ln_ENVARS_DIR")
    gv.config: dict                 = config
    gv.devicesDB: dict              = devicesDB
    gv.telegramMessage              = TelegramSendMessage_Class(devicesDB=devicesDB, logger=logger)
    gv.broker                       = devicesDB.getBroker()



    # savePidFile(args.pid_file)
    mqttClientMonitor.run(gVars=gv)
