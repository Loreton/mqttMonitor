#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os
import logging; logger=logging.getLogger(__name__)



def savePidFile(filename: str):
    pid=os.getpid()
    parent_dir=os.path.dirname(filename)
    os.makedirs(parent_dir,  exist_ok=True)
    with open(filename, "w") as f:
        f.write(f'{pid}')

    logger.info("pid file: %s has been created", filename)
