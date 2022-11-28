#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 28-11-2022 17.10.30

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)

import threading
from queue import Queue
import time
import json, yaml
import signal

from LnDict import LoretoDict
import SendTelegramMessage as STM

import Tasmota_Formatter as tasmotaFormatter
# import Tasmota_Formatter_V1_1 as tasmotaFormatter




def setup(my_logger):
    global logger
    logger=my_logger
    italicB='<i>'; italicE='</i>'


def from_telegram(topic: str, payload: (dict, str)=None, devices: dict=None):
    _dict=LoretoDict()
    _loreto=LoretoDict(device['Loreto'])
    relayNames=_loreto['friendly_names']

    command=payload.get('command')
    if command=='summary'
        _dict.update(tasmotaFormatter.deviceInfo(data=_loreto))
        _dict['Wifi']=tasmotaFormatter.wifi(data=_loreto["Wifi"])
        _dict['Wifi']['Mac']=f"{italicB}{_loreto['Mac']}{italicE}"
        _dict['Wifi']['IPAddress']=f"{italicB}{_loreto['IPAddress']}{italicE}"

        for index, name in enumerate(relayNames):
            pt_value, pt_remaining=tasmotaFormatter.getPulseTime(data=_loreto, relayNr=index)
            timers_status=tasmotaFormatter.timers(data=device['RESULT'], outputRelay=index+1, italic=True)

            _dict[name]={}
            _dict[name]["Pulsetime"]=f"{italicB}{pt_value}{italicE}"
            _dict[name]["Remaining"]=f"{italicB}{pt_remaining}{italicE}"
            _dict[name]["Status"]=f"{italicB}{_loreto[name]}{italicE}"
            _dict[name]["Timers"]=f"{italicB}{timers_status}{italicE}"


    elif command=="mqtt":
        _dict.update(tasmotaFormatter.deviceInfo(data=_loreto))
        _data=device["STATUS6.StatusMQT"]

        _mqtt=f'''MQTT:
                Host:   {italicB}{_data['MqttHost']}{italicE}
                Port:   {italicB}{_data['MqttPort']}{italicE}
                User:   {italicB}{_data['MqttUser']}{italicE}
                Client: {italicB}{_data['MqttClient']}{italicE}
                '''
        _dict=yaml.load(_mqtt , Loader=yaml.SafeLoader)


    else:
        _dict={"Response": f"command: {command} not implemented"}

        # _dict={"MQTT": {
        #                     'Host': f"{italicB}{_data['MqttHost']}{italicE}",
        #                     'Port': f"{italicB}{_data['MqttPort']}{italicE}",
        #                     'User': f"{italicB}{_data['MqttUser']}{italicE}",
        #                     'Client': f"{italicB}{_data['MqttClient']}{italicE}",
        #                 }
        #         }

    ### Power ON
    # elif command in ["on1", "on2"]:
    #     index=int(command[-1])

    #     topic=f'cmnd/{topic_name}/backlog'
    #     _payload=f'power{index} on'
    #     result=mqttClient_CB.publish(topic=topic, payload=_payload, qos=0, retain=False)
    #     _dict={"command": _payload,
    #             "topic": topic,
    #             "action": "executed",
    #     }

    # ### Power OFF
    # elif command in ["off1", "off2"]:
    #     index=int(command[-1])

    #     topic=f'cmnd/{topic_name}/backlog'
    #     _payload=f'power{index} off'
    #     result=mqttClient_CB.publish(topic=topic, payload=_payload, qos=0, retain=False)
    #     _dict={"command": _payload,
    #             "topic": topic,
    #             "action": "executed",
    #     }



    return _dict


######################################################
# process topic name and paylod data to findout query,
#
# LnCmnd/topic/tg_command
#    payload={'command': backlog}
#    payload={'command': summary}
#    payload={'command': pulsetime}
#
# LnCmnd/topic/tg_response
#    payload={'result': data}
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


    ### LnCmnd/topic_name/tg_command
    if suffix=='tg_command':
        _dict=from_telegram(topic=topic, payload=payload, devices=devices)


    elif suffix=='timers_in_payload':
        for index, name in enumerate(relayNames):
            _dict[name]={}
            _dict[name]['Timers']=tasmotaFormatter.timers(data=payload, outputRelay=index+1)




    ### Tested
    elif suffix=='power_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        key=list(payload.keys())[0] # dovrebbe essere POWERx
        index=int(key[-1])
        name=relayNames[index-1]
        _dict[name]={}
        _dict[name]['Status']=payload[key]



    ### Testedd
    elif suffix=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        for index, name in enumerate(relayNames):
            pt_value, pt_remaining=tasmotaFormatter.getPulseTime(data=payload, relayNr=index)
            _dict[name]={}
            _dict[name]["Pulsetime"]=pt_value
            _dict[name]["Remaining"]=pt_remaining

    elif suffix=='ssid_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
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





