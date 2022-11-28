#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 28-11-2022 17.25.52

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os


import threading
from queue import Queue
import time
import json, yaml
import signal

from LnDict import LoretoDict
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
def telegram_notify(topic: str, payload: (dict, str)=None, devices: dict=None):
    logger.info('processing topic %s for telegram message', topic)
    _,  topic_name, suffix=topic.split('/')


    if topic_name in devices:
        device=devices[topic_name]
    else:
        logger.error("topic_name: %s not found in devives", topic_name)
        return

    if 'STATE' not in device or 'sensors' not in device:
        logger.warning('%s - non discovered too', topic_name)
        return




    _dict=LoretoDict()
    _loreto=LoretoDict(device['Loreto'])
    relayNames=_loreto['friendly_names']
    italicB='<i>'; italicE='</i>'

    if suffix=='summary':  ### LnCmnd/topic_name/summary
        logger.notify("%s - I'm in 'summary' routine", topic_name)
        _dict.update(tasmotaFormatter.deviceInfo(data=_loreto))
        _dict['Wifi']=tasmotaFormatter.wifi(data=_loreto["Wifi"])
        _dict['Wifi']['Mac']=f"{italicB}{_loreto['Mac']}{italicE}"
        _dict['Wifi']['IPAddress']=f"{italicB}{_loreto['IPAddress']}{italicE}"

        for index, name in enumerate(relayNames):
            pt_value, pt_remaining=tasmotaFormatter.getPulseTime(data=_loreto, relayNr=index)
            timers_status=tasmotaFormatter.timers(data=device['RESULT'], outputRelay=index+1)

            _dict[name]={}
            _dict[name]["Pulsetime"]=f"{italicB}{pt_value}{italicE}"
            _dict[name]["Remaining"]=f"{italicB}{pt_remaining}{italicE}"
            _dict[name]["Status"]=f"{italicB}{_loreto[name]}{italicE}"
            _dict[name]["Timers"]=f"{italicB}{timers_status}{italicE}"


    elif suffix=="mqtt":  ### LnCmnd/topic_name/mqtt
        logger.notify("%s - I'm in 'mqtt' routine", topic_name)
        _dict.update(tasmotaFormatter.deviceInfo(data=_loreto))
        _data=device["STATUS6.StatusMQT"]

        _dict={"MQTT": {
                            'Host': f"{italicB}{_data['MqttHost']}{italicE}",
                            'Port': f"{italicB}{_data['MqttPort']}{italicE}",
                            'User': f"{italicB}{_data['MqttUser']}{italicE}",
                            'Client': f"{italicB}{_data['MqttClient']}{italicE}",
                        }
                }

    elif suffix=='timers_in_payload':
        logger.notify("%s - I'm in 'timers_in_payload' routine", topic_name)
        for index, name in enumerate(relayNames):
            _dict[name]={}
            _dict[name]['Timers']=tasmotaFormatter.timers(data=payload, outputRelay=index+1)




    ### Tested
    elif suffix=='XXXpower_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        logger.notify("%s - I'm in 'power_in_payload' routine", topic_name)
        key=list(payload.keys())[0] # dovrebbe essere POWERx
        index=int(key[-1])
        name=relayNames[index-1]
        _dict[name]=payload[key]



    ### Tested {"POWER1":"OFF"}
    elif suffix=='power_in_payload':
        logger.notify("%s - I'm in 'power_in_payload' routine", topic_name)

        ### catturiamo lo status
        key=list(payload.keys())[0] # dovrebbe essere POWERx
        new_status=payload[key]  # value ON, OFF

        ### catturiamo l'indice del relay
        index=int(key[-1])   ### 1,2,...
        friendly_name=relayNames[index-1] # friendly_name

        ### scan friendly names
        for index, name in enumerate(relayNames):
            name=relayNames[index-1]
            if name==friendly_name:
                _dict[name]=f"{italicB}{new_status}{italicE}"
            else:
                _dict[name]=f"{italicB}{_loreto[name]}{italicE}"





    ### Testedd
    elif suffix=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        logger.notify("%s - I'm in 'pulsetime_in_payload' routine", topic_name)
        for index, name in enumerate(relayNames):
            pt_value, pt_remaining=tasmotaFormatter.getPulseTime(data=payload, relayNr=index)
            _dict[name]={}
            _dict[name]["Pulsetime"]=pt_value
            _dict[name]["Remaining"]=pt_remaining




    elif suffix=='ssid_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        logger.notify("%s - I'm in 'ssid_in_payload' routine", topic_name)
        _dict=payload

    else:
        return





    # fTELEGRAM_NOTIFICATION=(time.time()-notification_timer_OLD[topic_name])>5 # ignore topic messages when notification_timer_OLD is running
    fTELEGRAM_NOTIFICATION=(time.time()-device["notification_timer"])>10 # ignore topic messages when notification_timer_OLD is running


    if _dict and fTELEGRAM_NOTIFICATION:
        tg_msg=LoretoDict({topic_name: _dict })
        logger.notify('sending telegram message: %s', tg_msg)

        ### parse_mode=None altrimenti mi da errore oppure html ma con attenzione:
        ### response: {'ok': False, 'error_code': 400, 'description': "Bad Request: can't parse entities: Can't find end of the entity starting at byte offset 493"}
        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode=None, notify=True)

        STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode='html', notify=True)





