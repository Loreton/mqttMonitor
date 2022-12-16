#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 16-12-2022 15.16.18

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os


import threading
from queue import Queue
import time
import json, yaml
import signal

# from LoretoDict import LnDict
import SendTelegramMessage as STM

# import Tasmota_Formatter as tasmotaFormatter
from benedict import benedict




def setup(*, gVars):
    global gv, logger
    gv=gVars
    logger=gv.logger





######################################################
# process topic name and paylod data to findout query,
#
# topic='LnCmnd/topic_name/query' (comando esterno)
#      payload="summary"
#      payload="timers"
#
# topic='LnCmnd/topic_name/summary'
#
######################################################
def telegram_notify(deviceObj, topic_name: str, action: str, payload: (dict, str)=None):
    logger.info('processing topic %s - %s ', topic_name, action)


    ### per i soli comandi non provenienti da Telegram
    tg_msg={
        gv.prj_name: {
            "command": action.replace('_in_payload', ''),
            }
        }

    ### dobbiamo attendere che il timer sia expired
    if '_in_payload' in action:
        if not deviceObj.telegramNotification():
            logger.warning("%s - %s skipping due to telegramNotification timer", topic_name, payload)
            return
        # tg_msg[gv.prj_name]['msg']="captured"

    # else:

    if isinstance(payload, dict):
        if 'debug' in payload and payload['debug'] is True: ### in caso di debug da telegram
            tg_msg[gv.prj_name]['msg']="has been received"
            STM.sendMsg(group_name=topic_name, message=tg_msg, my_logger=logger)
    else:
        logger.warning('%s - payload is not a dictionry: %s', topic_name, payload)
        return

    _dict={}

    for index in range(deviceObj.relays):
        relay_name=deviceObj.friendlyNames(index)

    relayNames=deviceObj.friendlyNames()

    #=====================================================================
    # actions from telegramBot
    #=====================================================================
    if action=='summary':  ### LnCmnd/topic_name/summary
        _dict.update(deviceObj.Info(italic=True))
        _dict['Wifi']=deviceObj.wifi(italic=True)

        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(index=index, italic=True)
            relay_name=f'fn_{relay_name}'
            _dict[relay_name]={}
            _dict[relay_name]["Status"]=deviceObj.relayStatus(relay_nr=relay_nr, italic=True)
            _dict[relay_name]["Pulsetime"]=pt_value
            _dict[relay_name]["Remaining"]=pt_remaining
            _dict[relay_name]["Timers"]=deviceObj.timersToHuman(relay_nr=relay_nr, italic=True)


    elif action=="mqtt":  ### LnCmnd/topic_name/mqtt
        _dict.update(deviceObj.Info(italic=True))
        _dict=deviceObj.mqtt(italic=True)


    elif action in ["version", "firmware"]:  ### LnCmnd/topic_name/version
        _dict=deviceObj.firmware(italic=True)


    elif action=="net_status":  ### LnCmnd/topic_name/mqtt
        _dict=deviceObj.net_status(italic=True)





    #=====================================================================
    # actions from Topic_Process
    #=====================================================================
    elif action=='timers_in_payload':
        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            relay_name=f'fn_{relay_name}'
            _dict[relay_name]={}
            _dict[relay_name]['Status']=deviceObj.relayStatus(relay_nr=relay_nr, italic=True)
            _dict[relay_name]["Timers"]=deviceObj.timersToHuman(relay_nr=relay_nr, italic=True)


    ### Tested
    elif action=='power_in_payload':

        ### catturare solo  {"POWERx":"ON/OFF"}
        keys=list(payload.keys())
        if len(keys)==1:
            if keys[0].startswith('POWER'):
                ### scan friendly names
                for index, name in enumerate(relayNames):
                    name=f'fn_{name}'
                    relay_nr=index+1
                    _dict[name]={}
                    _dict[name]=deviceObj.relayStatus(relay_nr=relay_nr, italic=True)



    ### Tested
    elif action=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        for index, name in enumerate(relayNames):
            name=f'fn_{name}'
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(index=index, italic=True)
            _dict[name]={}
            _dict[name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"


    elif action=='poweronstate_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        value=payload['PowerOnState']
        _values=["OFF", "ON", "TOGGLE", "Last State", "ON + disable power control", "Inverted PulseTime"]
        _dict["PowerOnState"]=_values[int(value)]


    elif action in ['ssid_in_payload']:     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        _dict=payload

    elif action in ["ipaddress_in_payload"]:     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        _dict=deviceObj.net_status(payload=payload)

    else:
        return



    if _dict:
        # tg_msg=benedict({topic_name: _dict }, keypath_separator='/')
        tg_msg=benedict(_dict, keypath_separator='/')

        logger.notify('sending telegram message: %s', tg_msg)

        ### parse_mode=None altrimenti mi da errore oppure html ma con attenzione:
        ### response: {'ok': False, 'error_code': 400, 'description': "Bad Request: can't parse entities: Can't find end of the entity starting at byte offset 493"}
        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode=None, notify=True)

        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode='html', notify=True)
        STM.sendMsg(group_name=topic_name, message=tg_msg, my_logger=logger, caller=True, parse_mode='html', notify=True)





