#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 19-02-2024 18.44.16

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os


import threading
from queue import Queue
import time
import json, yaml
import signal
from benedict import benedict
from types import SimpleNamespace

import dictUtils
import Tasmota_Human_Converter as THC
from Tasmota_Class import TasmotaClass # solo per typing




#####################################
# gVars is benedict dictionary
#####################################
def setup(gVars: dict):
    global gv, C
    gv=gVars
    C=gv.logger.getColors()
    THC.setup(gVars)



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
def in_payload_notify(tasmotaObj, action: str, payload: (dict, str)=None):
    topic_name=tasmotaObj.device_name
    gv.logger.info('processing topic %s - %s ', topic_name, action, stacklevel=2)

    telegramReplyMsg={"tg_notify": False}

    ### dobbiamo attendere che il timer sia expired
    if '_in_payload' in action:
        if not tasmotaObj.telegramNotification():
            gv.logger.warning("skipping due to telegramNotification timer - %s - %s", topic_name, payload)
            return



    # for index in range(tasmotaObj.relays):
    #     relay_name=tasmotaObj.friendlyNames(index)

    relayNames=tasmotaObj.friendlyNames()

    #=====================================================================
    # actions from Topic_Process
    # @LnToDo:  03-03-2023 inserire il display del pulseTime
    #=====================================================================
    if action=='timers_in_payload':
        _timers_data=tasmotaObj.timers()

        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            relay_name=f'relay_{relay_name}'
            telegramReplyMsg[relay_name]={}
            telegramReplyMsg[relay_name]['Status']=tasmotaObj.relayStatus(relay_nr=relay_nr)
            # @ToDo:  15-03-2023 verificare timer di VescoviNew
            telegramReplyMsg[relay_name]["Timers"]=THC.timersToHuman(timers_data=_timers_data, relay_nr=relay_nr)

            pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=tasmotaObj.pulsetime(), relay_nr=relay_nr, strip_leading=True)
            if pt_value!=0:
                telegramReplyMsg[relay_name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"


    ### display nudo e crudo del timerX
    elif action=='single_timer_in_payload':
        telegramReplyMsg=payload
        keys=list(telegramReplyMsg.keys())
        if len(keys)==1:
            ptr=telegramReplyMsg[keys[0]]
            if 'Mode' in ptr: ptr.pop('Mode')
            if 'Window' in ptr: ptr.pop('Window')


    elif action=='power_in_payload':
        ### dobbiamo catturare solo  {"POWERx":"ON/OFF"}
        keys=list(payload.keys())
        if len(keys)==1:
            if keys[0].startswith('POWER'):
                telegramReplyMsg={"tg_notify": True}
                cur_relay=int(keys[0].split('POWER')[1])
                for index, relay_name in enumerate(relayNames):  ### scan friendly names
                    relay_nr=index+1
                    relay_name=f'relay_{relay_name}'
                    telegramReplyMsg[relay_name]={}
                    if relay_nr==cur_relay:
                        telegramReplyMsg[relay_name]['Status']=payload[keys[0]]
                    else:
                        telegramReplyMsg[relay_name]['Status']=tasmotaObj.relayStatus(relay_nr=relay_nr)
                    # if topic_name=="VescoviNew":
                    #     import pdb; pdb.set_trace();trace=True # by Loreto
                    #     xx=0
                    pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=tasmotaObj.pulsetime(), relay_nr=relay_nr, strip_leading=True)

                    if pt_value!=0:
                        telegramReplyMsg[relay_name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"



        else:
            gv.logger.warning('payload non contiene keys: %s - %s', type(payload), payload)


    ### Tested
    elif action=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        for index, relay_name in enumerate(relayNames):
            relay_nr=index+1
            name=f'relay_{relay_name}'
            pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=tasmotaObj.pulsetime(), relay_nr=relay_nr, strip_leading=True)

            telegramReplyMsg[relay_name]={}
            telegramReplyMsg[relay_name]["Pulsetime"]=f"{pt_value} ({pt_remaining})"


    elif action=='poweronstate_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        value=payload['PowerOnState']
        _values=["OFF", "ON", "TOGGLE", "Last State", "ON + disable power control", "Inverted PulseTime"]
        telegramReplyMsg["PowerOnState"]=_values[int(value)]


    elif action in ['ssid_in_payload']:     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        telegramReplyMsg=payload

    elif action in ["ipaddress_in_payload"]:     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
        telegramReplyMsg=tasmotaObj.net_status(payload=payload)

    else:
        return

    # notify_telegram_group(topic_name=topic_name, data=telegramReplyMsg)
    notify_telegram_group(tasmotaObj=tasmotaObj, data=telegramReplyMsg)






######################################################
# topic='LnTelegram/topic_name/alias' (comando esterno)
#      payload['alias']="summary" or other....
#
######################################################
def telegram_notify(tasmotaObj: TasmotaClass, payload: (dict, str)=None):
    topic_name=tasmotaObj.device_name
    gv.logger.info('processing topic %s - payload: %s ', topic_name, str(payload))

    if isinstance(payload, dict):
        if 'debug' in payload and payload['debug'] is True: ### in caso di debug da telegram
            tg_msg[gv.prj_name]['msg']="has been received"
            gv.telegramMessage.send_html(tg_group=tasmotaObj.tg(), message=tg_msg) # @ToDo:  10-10-2023 tg_group deve essere un dictionary
    else:
        gv.logger.warning('%s - payload is not a dictionary: %s', topic_name, payload)
        return

    alias=payload["alias"]
    telegramReplyMsg={"tg_notify": False}


    #=====================================================================
    # actions from telegramBot
    #=====================================================================
    if alias in ['summary', 'status']:
        telegramReplyMsg.update(tasmotaObj.generalInfo())
        telegramReplyMsg['Wifi']=tasmotaObj.wifi()
        _timers_data=tasmotaObj.timers()

        for index, relay_name in enumerate(tasmotaObj.friendlyNames()):
            relay_nr=index+1
            pt_value, pt_remaining=THC.pulseTimeToHuman(pulsetime_data=tasmotaObj.pulsetime(), relay_nr=relay_nr, strip_leading=True)
            # pt_value, pt_remaining=tasmotaObj.pulseTimeToHuman(relay_nr=index) ### parte da '0''

            relay_name=f'relay_{relay_name}'
            relay_nr=index+1
            telegramReplyMsg[relay_name]={}
            telegramReplyMsg[relay_name]["Status"]=tasmotaObj.relayStatus(relay_nr=relay_nr)
            telegramReplyMsg[relay_name]["Pulsetime"]=pt_value
            telegramReplyMsg[relay_name]["Remaining"]=pt_remaining
            telegramReplyMsg[relay_name]["Timers"]=THC.timersToHuman(timers_data=_timers_data, relay_nr=relay_nr)


    elif alias=="mqtt":  ### LnTelegram/topic_name/mqtt
        telegramReplyMsg.update(tasmotaObj.generalInfo())
        telegramReplyMsg.update(tasmotaObj.mqttInfo())


    elif alias in ["version", "firmware"]:  ### LnTelegram/topic_name/version
        telegramReplyMsg=tasmotaObj.firmware()


    elif alias=="net_status":  ### LnTelegram/topic_name/mqtt
        telegramReplyMsg=tasmotaObj.net_status()


    if telegramReplyMsg:
        notify_telegram_group(tasmotaObj=tasmotaObj, data=telegramReplyMsg)



############################################################
#
############################################################
def notify_telegram_group(tasmotaObj: TasmotaClass, data: (dict, str)):
    tg_notify=False

    if isinstance(data, dict):
        if "tg_notify" in data:
            tg_notify=data.pop("tg_notify")

        tg_msg=benedict(data, keypath_separator='§') ### potrebbe esserci il '.' da qualche parte e lo '/' non va bene per il parsemode 'html'
        gv.logger.notify('tg_msg: %s', tg_msg.to_json())

        gv.logger.notify('sending telegram message: %s', tg_msg)
        tg_msg=dictUtils.dict_bold_italic(tg_msg, keys='bold', values='italic', nlevels=2)
    else:
        tg_msg=data

    # gv.telegramMessage.send_html(tg_group=topic_name, message=tg_msg, caller=True, notify=tg_notify) # @ToDo:  10-10-2023 tg_group deve essere un dictionary
    gv.telegramMessage.send_html(tg_group=tasmotaObj.tg(), message=tg_msg, caller=True, notify=tg_notify) # @ToDo:  10-10-2023 tg_group deve essere un dictionary

