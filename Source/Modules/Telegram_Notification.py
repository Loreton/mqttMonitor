#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 11-12-2022 12.10.36

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os


import threading
from queue import Queue
import time
import json, yaml
import signal

from LoretoDict import LnDict
import SendTelegramMessage as STM

# import Tasmota_Formatter as tasmotaFormatter




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

    if '_in_payload' in action:
        if not deviceObj.telegramNotification():
            logger.warning("%s - %s skipping due to telegramNotification timer", topic_name, payload)
            return
        tg_msg[gv.prj_name]['msg']="captured"

    else:
        tg_msg[gv.prj_name]['msg']="has been received"

    if 'debug' in payload and payload['debug'] is True:
        STM.sendMsg(group_name=topic_name, message=tg_msg, my_logger=logger)

    _dict={}
    relayNames=deviceObj.friendlyNames

    #=====================================================================
    # actions from telegramBot
    #=====================================================================
    if action=='summary':  ### LnCmnd/topic_name/summary
        _dict.update(deviceObj.Info(italic=True))
        _dict['Wifi']=deviceObj.wifi(italic=True)

        for index, name in enumerate(relayNames):
            relay_nr=index+1
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(index=index, italic=True)

            _dict[name]={}
            _dict[name]["Status"]=deviceObj.relayStatus(relay_nr=relay_nr, italic=True)
            _dict[name]["Pulsetime"]=pt_value
            _dict[name]["Remaining"]=pt_remaining
            _dict[name]["Timers"]=deviceObj.timersToHuman(relay_nr=relay_nr, italic=True)


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
        for index, name in enumerate(relayNames):
            relay_nr=index+1
            _dict[name]={}
            _dict[name]['Status']=deviceObj.relayStatus(relay_nr=relay_nr, italic=True)
            _dict[name]["Timers"]=deviceObj.timersToHuman(relay_nr=relay_nr, italic=True)
            # _dict[name]=[]
            # _dict[name].append(deviceObj.relayStatus(relay_nr=index+1, italic=True))
            # _dict[name].append(deviceObj.timersToHuman(relay_nr=index+1, italic=True))


    ### Tested
    elif action=='power_in_payload':

        ### catturare solo  {"POWERx":"ON/OFF"}
        keys=list(payload.keys())
        if len(keys)==1:
            if keys[0].startswith('POWER'):
                ### scan friendly names
                for index, name in enumerate(relayNames):
                    relay_nr=index+1
                    _dict[name]={}
                    _dict[name]=deviceObj.relayStatus(relay_nr=relay_nr, italic=True)



    ### Tested
    elif action=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        for index, name in enumerate(relayNames):
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
        tg_msg=LnDict({topic_name: _dict })
        logger.notify('sending telegram message: %s', tg_msg)

        ### parse_mode=None altrimenti mi da errore oppure html ma con attenzione:
        ### response: {'ok': False, 'error_code': 400, 'description': "Bad Request: can't parse entities: Can't find end of the entity starting at byte offset 493"}
        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode=None, notify=True)

        STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode='html', notify=True)





