#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os

from benedict import benedict
from pathlib import Path

## Project modules
os.environ['Loader_modules']="csv ini yaml json"
import Source
import prepare_gVars
import LnUtils
import FileLoader
import mqttClientMonitor

from ColoredLogger import setColoredLogger, testLogger
from ParseInput import ParseInput
# from savePidFile import savePidFile


from    devicesDB_sqLite import devicesDB_Class
import  FileLoader
import  prepare_gVars


#=======================================
# - Project modules
#=======================================
project_log_levels={
    "critical": 50,
    "error":    40,
    "warning":  30,
    "notify":   25,
    "info":     20,
    "function": 18,
    "caller":   15,
    "debug":    10,
    "trace":    5,
    "notset":   0,
}

# verificare le strutture del DB
# eliminare tutti i TG groups che non servono
# ovviamente mettere un controllo nle programma pre prendere in consoiderazione solo quelli che hanno, ad esempio, un chat_id
#######################################################
#
#######################################################
if __name__ == '__main__':
    prj_env = "mqtt"
    prj_name="mqttMonitor"
    __ln_version__=f"{prj_name} version: V2024-05-25_073116"
    args=ParseInput(__ln_version__)

    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir, # logging file--> logging_dir + logger_name
                            threads=False,
                            create_logging_dir=True,
                            prj_log_levels=project_log_levels)


    # testLogger()

    logger.info('------- Starting -----------')
    logger.warning(__ln_version__)

    os.environ["PRJ_ENV"] = f"{args.project_env}/D202405"

    # ----- prepare global project variables
    gv=prepare_gVars.setMainVars(logger=logger, input_args=args, prj_name=prj_name, search_paths=["conf", "links_conf"])



    # -------------------------------
    # ----- Load configuration data
    # -------------------------------
    os.environ["DB_NAME"]="devicesDB"
    config_file=f"{prj_name}_config.yaml"
    gv.exit_on_config_file_not_found=True

    unresolved_fileout=f"{gv.tmp_dir}/unresolved_full_config.yaml"
    if not (full_config:=FileLoader.loadConfigurationData(config_file=config_file, save_yaml_on_file=unresolved_fileout) ):
        logger.error("Configuration data error")
        sys.exit(1)
    # os.system(f"/usr/bin/subl {unresolved_fileout}")

    sqlite_config = full_config.pop("sqlite") ### extrai la parte sqlite

    main_config=full_config.pop("main") ### extrai la parte sqlite


    mqttClientMonitor.run(gVars=gv, main_config=main_config, sqlite_config=sqlite_config)

