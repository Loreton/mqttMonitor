#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 18-11-2022 12.22.24


import  sys; sys.dont_write_bytecode = True
import  os
import logging; logger=logging.getLogger(__name__)

from pathlib import Path



# -------------------------
# - Load syspath with custom modules paths in modo
# - da poter richiamare facilmente i moduli con il solo nome
# - anche con il progetto zipped
# -------------------------
_my_path=[]
def set_path():

    def _include_path(path):
        if os.path.exists(path):
            _my_path.append(path)

    script_name=Path(sys.argv[0]).resolve()

    if script_name.suffix == '.zip': # sono all'interno dello zip
        _my_path.append(script_name.parent.parent)
        prj_dir=script_name # ... nome dello zip_file
        # my_path.extend(extractZip(script_name)) # extract lnLib.zip from project.zip file and get its path
    else:
        prj_dir=script_name.parent # nome della prj directory
        _my_path.append(script_name.parent)

    _include_path(prj_dir)
    _include_path(f'{prj_dir}/Source')
    _include_path(f'{prj_dir}/Source/Main')
    _include_path(f'{prj_dir}/Source/LnLib')
    _include_path(f'{prj_dir}/Source/Modules')
    _include_path(f'{prj_dir}/Source/Mqtt')
    _include_path(f'{prj_dir}/Source/LnLib.zip')

    for path in reversed(_my_path):
        # print(str(path))
        sys.path.insert(0, str(path))


if not _my_path: set_path()

