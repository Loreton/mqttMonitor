#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 30-01-2023 08.59.35



import sys
from pathlib import Path


# -------------------------
# - Load syspath with custom modules paths in modo
# - da poter richiamare facilmente i moduli con il solo nome
# - anche con il progetto zipped
# -------------------------
_my_path=[]
def set_path():
    script_name=Path(sys.argv[0]).resolve()

    if script_name.suffix == '.zip': # sono all'interno dello zip
        _my_path.append(script_name.parent.parent)
        prj_dir=script_name # ... nome dello zip_file
        # my_path.extend(extractZip(script_name)) # extract lnLib.zip from project.zip file and get its path
    else:
        prj_dir=script_name.parent # nome della prj directory
        _my_path.append(script_name.parent)

    _my_path.append(prj_dir)
    _my_path.append(f'{prj_dir}/Source')
    _my_path.append(f'{prj_dir}/Source/Main')
    _my_path.append(f'{prj_dir}/Source/Modules')
    _my_path.append(f'{prj_dir}/Source/lnLib')
    # _my_path.append(f'{prj_dir}/Source/LnLib.zip')

    for path in _my_path:
        sys.path.insert(0, str(path))

if not _my_path: set_path()

