#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 25-02-2023 18.31.09

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os


import threading
from queue import Queue
import time
import json, yaml
import signal
from benedict import benedict

from LnUtils import dict_bold_italic
import Tasmota_Human_Converter as THC



def setup(*, gVars):
    global gv
    gv=gVars





######################################################
# process topic name and paylod data to findout query,
#
# topic='LnTelegram/topic_name/query' (comando esterno)
#      payload="summary"
#      payload="timers"
#
# topic='LnTelegram/topic_name/summary'
#
######################################################
def in_payload_notify(deviceObj, topic_name: str, action: str, payload: (dict, str)=None):
    gv.logger.info('processing topic %s - %s ', topic_name, action)

    tg_msg={
        gv.prj_name: {
            "command": action.replace('_in_payload', ''),
            }
        }

    ### dobbiamo attendere che il timer sia expired
    if '_in_payload' in action:
        if not deviceObj.telegramNotification():
            gv.logger.warning("skipping due to telegramNotification timer - %s - %s", topic_name, payload)
            return


    _dict={}

    for index in range(deviceObj.relays):
        relay_name=deviceObj.friendlyNames(index)

    relayNames=deviceObj.friendlyNames()

    #=====================================================================
    # actions from Topic_Process
    #=====================================================================
    if action=='timers_in_payload':
        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            relay_name=f'relay_{relay_name}'
            _dict[relay_name]={}
            _dict[relay_name]['Status']=deviceObj.relayStatus(relay_nr=relay_nr)
            _dict[relay_name]["Timers"]=deviceObj.timersToHuman(relay_nr=relay_nr)

    ### display nudo e crudo del timerX
    elif action=='single_timer_in_payload':
        _dict=payload
        keys=list(_dict.keys())
        if len(keys)==1:
            ptr=_dict[keys[0]]
            if 'Mode' in ptr: ptr.pop('Mode')
            if 'Window' in ptr: ptr.pop('Window')


    ### Tested
    elif action=='power_in_payload':
        ### catturare solo  {"POWERx":"ON/OFF"}
        keys=list(payload.keys())
        if len(keys)==1:
            if keys[0].startswith('POWER'):
                cur_relay=int(keys[0].split('POWER')[1])
                for index, relay_name in enumerate(relayNames):  ### scan friendly names
                    relay_name=f'relay_{relay_name}'
                    relay_nr=index+1
                    _dict[relay_name]={}
                    if relay_nr==cur_relay:
                        _dict[relay_name]=payload[keys[0]]
                    else:
                        _dict[relay_name]=deviceObj.relayStatus(relay_nr=relay_nr)




        else:
            print('NO NON.........................ci sono', payload)


    ### Tested
    elif action=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        for relay_nr, name in enumerate(relayNames):
            name=f'relay_{name}'
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(relay_nr=relay_nr)
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

    notify_telegram_group(topic_name=topic_name, action=action, data=_dict)






######################################################
# process topic name and paylod data to findout query,
#
# topic='LnTelegram/topic_name/telegram' (comando esterno)
#      payload="summary"
#      payload="timers"
#
# topic='LnTelegram/topic_name/summary'
#
######################################################
def telegram_notify(deviceObj, topic_name: str, action: str, payload: (dict, str)=None):
    gv.logger.info('processing topic %s - %s ', topic_name, action)

    if isinstance(payload, dict):
        if 'debug' in payload and payload['debug'] is True: ### in caso di debug da telegram
            tg_msg[gv.prj_name]['msg']="has been received"
            gv.telegramMessage.send(group_name=topic_name, message=tg_msg)
    else:
        gv.logger.warning('%s - payload is not a dictionary: %s', topic_name, payload)
        return

    alias=payload["alias"]
    _dict={}

    relayNames=deviceObj.friendlyNames()

    #=====================================================================
    # actions from telegramBot
    #=====================================================================
    if alias in ['summary', 'status']:
        _dict.update(deviceObj.Info())
        _dict['Wifi']=deviceObj.wifi()

        for index, relay_name in enumerate(relayNames):
            pt_value, pt_remaining=deviceObj.pulseTimeToHuman(relay_nr=index) ### parte da '0''
            relay_name=f'relay_{relay_name}'
            relay_nr=index+1
            _dict[relay_name]={}
            _dict[relay_name]["Status"]=deviceObj.relayStatus(relay_nr=relay_nr)
            _dict[relay_name]["Pulsetime"]=pt_value
            _dict[relay_name]["Remaining"]=pt_remaining
            _dict[relay_name]["Timers"]=deviceObj.timersToHuman(relay_nr=relay_nr)


    elif alias=="mqtt":  ### LnTelegram/topic_name/mqtt
        _dict.update(deviceObj.Info())
        _dict=deviceObj.mqtt()


    elif alias in ["version", "firmware"]:  ### LnTelegram/topic_name/version
        _dict=deviceObj.firmware()


    elif alias=="net_status":  ### LnTelegram/topic_name/mqtt
        _dict=deviceObj.net_status()


    notify_telegram_group(topic_name=topic_name, action=alias, data=_dict)



############################################################
#
############################################################
def notify_telegram_group(topic_name: str, action: str, data: (dict, str)):
    if data:
        if isinstance(data, dict):
            tg_msg=benedict(data, keypath_separator='§') ### potrebbe esserci il '.' da qualche parte e lo '/' non va bene per il parsemode 'html'
            gv.logger.notify('tg_msg: %s', tg_msg.to_json())

            gv.logger.notify('sending telegram message: %s', tg_msg)
            tg_msg=dict_bold_italic(tg_msg, keys='bold', values='italic', nlevels=2)
        else:
            tg_msg=data

        ### parse_mode=None altrimenti mi da errore oppure html ma con attenzione:
        ### response: {'ok': False, 'error_code': 400, 'description': "Bad Request: can't parse entities: Can't find end of the entity starting at byte offset 493"}
        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode=None, notify=True)

        # STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger, caller=True, parse_mode='html', notify=True)

        gv.telegramMessage.send_html(group_name=topic_name, message=tg_msg, caller=True, notify=True)
    else:
        # _dict={"Loreto": 'ciao'}
        # tg_msg=benedict(_dict, keypath_separator='/')
        # logger.notify('tg_msg: %s', tg_msg.to_json())
        # import pdb; pdb.set_trace(); pass # by Loreto
        gv.logger.notify('%s - no data found for %s', topic_name, action)
        # tg_msg=f'no data found for {action}'
        tg_msg={'error': f'no data found for {action}'}
        gv.telegramMessage.send_html(group_name=topic_name, message=tg_msg, caller=True, notify=True)





