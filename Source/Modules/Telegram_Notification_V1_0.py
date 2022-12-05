#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 05-12-2022 16.22.02

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

import Tasmota_Formatter as tasmotaFormatter




def setup(my_logger):
    global logger
    logger=my_logger





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
def telegram_notify(deviceObj, topic: str, payload: (dict, str)=None):
    logger.info('processing topic %s for telegram message', topic)
    _,  topic_name, suffix=topic.split('/')

    if not deviceObj.telegramNotification():
        return


    _dict={}
    # _loreto=LnDict(device['Loreto'])
    relayNames=deviceObj.friendlyNames()
    italicB='<i>'; italicE='</i>'

    if suffix=='summary':  ### LnCmnd/topic_name/summary
        logger.notify("%s - I'm in 'summary' routine", topic_name)
        _dict.update(deviceObj.Info(italic=True))
        _dict['Wifi']=deviceObj.wifi(italic=True)

        for index, name in enumerate(relayNames):
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(relay_nr=index, italic=True)

            _dict[name]={}
            _dict[name]["Status"]=deviceObj.relayStatus(relay_nr=index+1, italic=True)
            _dict[name]["Pulsetime"]=pt_value
            _dict[name]["Remaining"]=pt_remaining
            _dict[name]["Timers"]=deviceObj.timersToHuman(relay_nr=index+1, italic=True)


    elif suffix=="mqtt":  ### LnCmnd/topic_name/mqtt
        logger.notify("%s - I'm in 'mqtt' routine", topic_name)
        _dict.update(deviceObj.Info(italic=True))
        _dict=deviceObj.mqtt(italic=True)

    elif suffix=='timers_in_payload':
        logger.notify("%s - I'm in 'timers_in_payload' routine", topic_name)
        for index, name in enumerate(relayNames):
            _dict[name]={}
            _dict[name]['Status']=deviceObj.relayStatus(relay_nr=index+1, italic=True)
            _dict[name]["Timers"]=deviceObj.timersToHuman(relay_nr=index+1, italic=True)
            # _dict[name]=[]
            # _dict[name].append(deviceObj.relayStatus(relay_nr=index+1, italic=True))
            # _dict[name].append(deviceObj.timersToHuman(relay_nr=index+1, italic=True))


    ### Tested
    elif suffix=='power_in_payload':
        logger.notify("%s - I'm in 'power_in_payload' routine", topic_name)


        ### catturare solo  {"POWERx":"ON/OFF"}
        keys=list(payload.keys())
        if len(keys)==1:
            if keys[0].startswith('POWER'):
                ### scan friendly names
                for index, name in enumerate(relayNames):
                    _dict[name]={}
                    _dict[name]=deviceObj.relayStatus(relay_nr=index+1, italic=True)



    ### Testedd
    elif suffix=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        logger.notify("%s - I'm in 'pulsetime_in_payload' routine", topic_name)
        for index, name in enumerate(relayNames):
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(relay_nr=index, italic=True)
            _dict[name]={}
            _dict[name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"
            # _dict[name]["Pulsetime"]=pt_value
            # _dict[name]["Remaining"]=pt_remaining


    elif suffix=='poweronstate_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        logger.notify("%s - I'm in 'poweronstate_in_payload' routine", topic_name)
        _dict=payload


    elif suffix=='ssid_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        logger.notify("%s - I'm in 'ssid_in_payload' routine", topic_name)
        _dict=payload

    else:
        return



    if _dict:
        tg_msg=LnDict({topic_name: _dict })
        logger.notify('sending telegram message: %s', tg_msg)

        ### parse_mode=None altrimenti mi da errore oppure html ma con attenzione:
        ### response: {'ok': False, 'error_code': 400, 'description': "Bad Request: can't parse entities: Can't find end of the entity starting at byte offset 493"}
        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode=None, notify=True)

        STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode='html', notify=True)





