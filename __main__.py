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
    "function": 25,
    "info":     20,
    "notify":   18,
    "caller":   12,
    "debug":    10,
    "trace":    5,
    "notset":   0,
}

#######################################################
#
#######################################################
if __name__ == '__main__':
    os.environ["DB_FILE"] = "/home/loreto/lnProfile/config/devicesDB_sqLite/data_202405/devicesDB.sqlite_sample"

    prj_name=Path(sys.argv[0]).resolve().parent.stem
    __ln_version__=f"{prj_name} version: V2024-05-04_082239"
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

    sqlite_config=full_config.pop("sqlite") ### extrai la parte sqlite
    # sqlite_config.db_filepath = args.db_file

    main_config=full_config.pop("main") ### extrai la parte sqlite


    mqttClientMonitor.run(gVars=gv, main_config=main_config, sqlite_config=sqlite_config)

