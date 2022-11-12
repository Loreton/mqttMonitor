#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
from LnDict import LoretoDict



def set(my_logger):
    global logger, devices
    logger=my_logger
    devices=LoretoDict()


def process(topic, payload):
    # token=topic.split('/')
    prefix, device_name, suffix, *rest=topic.split('/')
    # device_name=token[1]

    ### create entry for device anem
    if not device_name in devices:
        devices[device_name]=LoretoDict()
        devices[device_name]['file_out']=os.path.expandvars(f"$ln_RUNTIME_DIR/mqtt_monitor/{device_name}.json")


    device=devices[device_name]
    fUPDATE=False
    if prefix == 'tele' and suffix=='STATE' \
            or prefix == 'stat' and suffix.startswith('STATUS') \
            or prefix == 'stat' and suffix.startswith('RESULT'):
        if not suffix in device:
            device[suffix]=payload
        else:
            device[suffix].update(payload)
        fUPDATE=True

    else:
        logger.notify(topic)
        logger.notify(payload)

        # if not suffix in device:
        #     device[suffix]=payload
        # else:
        #     device[suffix].update(payload)
        # fUPDATE=True


    if fUPDATE:
        logger.notify(topic)
        device.toJsonFile(file_out=device["file_out"], replace=True)





