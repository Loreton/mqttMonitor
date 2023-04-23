#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 23-04-2023 17.15.32

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
    gv.logger.info('processing topic %s - %s ', topic_name, action, stacklevel=2)

    tg_dictMsg={"tg_notify": False}

    ### dobbiamo attendere che il timer sia expired
    if '_in_payload' in action:
        if not deviceObj.telegramNotification():
            gv.logger.warning("skipping due to telegramNotification timer - %s - %s", topic_name, payload)
            # notify_telegram_group(topic_name=topic_name, action=action, data="please retry in a few seconds")
            return



    for index in range(deviceObj.relays):
        relay_name=deviceObj.friendlyNames(index)

    relayNames=deviceObj.friendlyNames()

    #=====================================================================
    # actions from Topic_Process
    # @LnToDo:  03-03-2023 inserire il display del pulseTime
    #=====================================================================
    if action=='timers_in_payload':
        # import pdb; pdb.set_trace(); pass # by Loreto
        # _timers=deviceObj.deviceDB.get('TIMERS')
        _timers_data=deviceObj.getDeviceDB('TIMERS')

        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            relay_name=f'relay_{relay_name}'
            tg_dictMsg[relay_name]={}
            tg_dictMsg[relay_name]['Status']=deviceObj.relayStatus(relay_nr=relay_nr)
            # @ToDo:  15-03-2023 verificare timer di VescoviNew
            tg_dictMsg[relay_name]["Timers"]=THC.timersToHuman(timers_data=_timers_data, relay_nr=relay_nr)

            pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=deviceObj.getDeviceDB('PulseTime'), relay_nr=relay_nr, strip_leading=True)
            if pt_value!=0:
                tg_dictMsg[relay_name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"


    ### display nudo e crudo del timerX
    elif action=='single_timer_in_payload':
        tg_dictMsg=payload
        keys=list(tg_dictMsg.keys())
        if len(keys)==1:
            ptr=tg_dictMsg[keys[0]]
            if 'Mode' in ptr: ptr.pop('Mode')
            if 'Window' in ptr: ptr.pop('Window')


    # @LnToDo:  03-03-2023 inserire il display del pulseTime
    elif action=='power_in_payload':
        ### dobbiamo catturare solo  {"POWERx":"ON/OFF"}
        keys=list(payload.keys())
        if len(keys)==1:
            if keys[0].startswith('POWER'):
                tg_dictMsg={"tg_notify": True}
                cur_relay=int(keys[0].split('POWER')[1])
                for index, relay_name in enumerate(relayNames):  ### scan friendly names
                    relay_nr=index+1
                    relay_name=f'relay_{relay_name}'
                    tg_dictMsg[relay_name]={}
                    if relay_nr==cur_relay:
                        tg_dictMsg[relay_name]['Status']=payload[keys[0]]
                    else:
                        tg_dictMsg[relay_name]['Status']=deviceObj.relayStatus(relay_nr=relay_nr)

                    pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=deviceObj.getDeviceDB('PulseTime'), relay_nr=relay_nr, strip_leading=True)

                    if pt_value!=0:
                        tg_dictMsg[relay_name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"



        else:
            print('NO NON.........................ci sono', payload)


    ### Tested
    elif action=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            name=f'relay_{relay_name}'
            pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=deviceObj.getDeviceDB('PulseTime'), relay_nr=relay_nr, strip_leading=True)

            tg_dictMsg[relay_name]={}
            tg_dictMsg[relay_name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"


    elif action=='poweronstate_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        value=payload['PowerOnState']
        _values=["OFF", "ON", "TOGGLE", "Last State", "ON + disable power control", "Inverted PulseTime"]
        tg_dictMsg["PowerOnState"]=_values[int(value)]


    elif action in ['ssid_in_payload']:     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        tg_dictMsg=payload

    elif action in ["ipaddress_in_payload"]:     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        tg_dictMsg=deviceObj.net_status(payload=payload)

    else:
        return

    notify_telegram_group(topic_name=topic_name, action=action, data=tg_dictMsg)






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
    tg_dictMsg={"tg_notify": False}

    relayNames=deviceObj.friendlyNames()

    #=====================================================================
    # actions from telegramBot
    #=====================================================================
    if alias in ['summary', 'status']:
        tg_dictMsg.update(deviceObj.Info())
        tg_dictMsg['Wifi']=deviceObj.wifi()
        _timers_data=deviceObj.getDeviceDB('TIMERS')

        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=deviceObj.getDeviceDB('PulseTime'), relay_nr=relay_nr, strip_leading=True)
            # pt_value, pt_remaining=deviceObj.pulseTimeToHuman(relay_nr=index) ### parte da '0''

            relay_name=f'relay_{relay_name}'
            relay_nr=index+1
            tg_dictMsg[relay_name]={}
            tg_dictMsg[relay_name]["Status"]=deviceObj.relayStatus(relay_nr=relay_nr)
            tg_dictMsg[relay_name]["Pulsetime"]=pt_value
            tg_dictMsg[relay_name]["Remaining"]=pt_remaining
            tg_dictMsg[relay_name]["Timers"]=THC.timersToHuman(timers_data=_timers_data, relay_nr=relay_nr)


    elif alias=="mqtt":  ### LnTelegram/topic_name/mqtt
        tg_dictMsg.update(deviceObj.Info())
        tg_dictMsg=deviceObj.mqtt()


    elif alias in ["version", "firmware"]:  ### LnTelegram/topic_name/version
        tg_dictMsg=deviceObj.firmware()


    elif alias=="net_status":  ### LnTelegram/topic_name/mqtt
        tg_dictMsg=deviceObj.net_status()


    notify_telegram_group(topic_name=topic_name, action=alias, data=tg_dictMsg)



############################################################
#
############################################################
def notify_telegram_group(topic_name: str, action: str, data: (dict, str)):
    tg_notify=False

    if data:
        if isinstance(data, dict):
            if "tg_notify" in data:
                tg_notify=data.pop("tg_notify")

            tg_msg=benedict(data, keypath_separator='§') ### potrebbe esserci il '.' da qualche parte e lo '/' non va bene per il parsemode 'html'
            gv.logger.notify('tg_msg: %s', tg_msg.to_json())

            gv.logger.notify('sending telegram message: %s', tg_msg)
            tg_msg=dict_bold_italic(tg_msg, keys='bold', values='italic', nlevels=2)
        else:
            tg_msg=data

        gv.telegramMessage.send_html(group_name=topic_name, message=tg_msg, caller=True, notify=tg_notify)

    else:
        gv.logger.notify('%s - no data found for %s', topic_name, action)
        tg_msg={'error': f'no data found for {action}'}
        gv.telegramMessage.send_html(group_name=topic_name, message=tg_msg, caller=True, notify=tg_notify)





