#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 14-05-2023 10.50.24

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
from types import SimpleNamespace
import threading
from queue import Queue
import time
import json, yaml
import signal
from benedict import benedict

import Tasmota_Telegram_Notification as tgNotify
from Tasmota_Class import TasmotaClass






def setup(gVars: SimpleNamespace):
    global gv
    gv=gVars
    # gv.devices=dict()
    # gv.macTable=dict()





#####################################################################
# process topic name and paylod data to find_out topic_name,
# topic='tasmota/discovery/DC4F22BE4445/sensors'
# topic='tasmota/discovery/DC4F22BE4445/config'
#
#  payload: {'sn': {'Time': '2022-11-04T20:45:58'}, 'ver': 1}
#
#  payload: {
#          "ip": "192.168.1.114",
#          "dn": "Crepuscolare", # device name
#          "fn": [
#              "Crepuscolare", # friendly name or relay0
#              null,
#              null,
#              null,
#              null,
#              null,
#              null,
#              null
#          ],
#          "hn": "Crepuscolare-1093",
#          "mac": "DC4F22BE4445"
#####################################################################
def tasmota_discovery_modify_topic(topic, mac_table, payload):
    _tasmota, _discovery, _mac,  suffix, *rest=topic.split('/')

    if _mac in mac_table:
        topic_name=gv.macTable[_mac]

    else:
        mac=payload.get('mac')
        topic_name=payload.get('t')
        if mac and topic_name:
            mac_table[mac]=topic_name # add to table

    topic=f'tasmota/{topic_name}/{suffix}'

    return topic






##########################################################
# Invia un summary status per tutti i device
##########################################################
def sendStatus():
    gv.logger.notify("Sending summary to Telegram")
    for topic_name in gv.devices.keys():
        gv.logger.notify("Sending summary for %s to Telegram", topic_name)
        tgNotify.telegram_notify(deviceObj=gv.devices[topic_name], topic_name=topic_name, payload={"alias": "summary"})






################################################
#-
################################################
def refreshDeviceData(topic_name: str, deviceObj, mqttClient_CB):
    deviceObj.telegramNotification(seconds=60) # temoporary stop to telegram notification
    _commands='state; power; status 0; timers; pulsetime; topic; teleperiod 30; SetOption26 1'
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', _commands, qos=0, retain=False)



#########################################################
# TEST:
#    cmnd/TavoloLavoro/bcacklog power
#    cmnd/TavoloLavoro/bcacklog timers
#########################################################

#########################################################
#  Per comodità cerco di utilizzare il topic_name==Device_name
#########################################################
def process(topic, payload, mqttClient_CB):
    gv.logger.info('processing topic: %s', topic)
    gv.logger.info('   payload: %s - %s', type(payload), payload)


    ### viene rilasciato automaticamente da tasmota
    if topic.startswith("tasmota/discovery"):
        """ topic='tasmota/discovery/DC4F22D3B32F/sensors'
            topic='tasmota/discovery/DC4F22D3B32F/config'
            cambiare il topic attraverso il MAC """
        topic=tasmota_discovery_modify_topic(topic, gv.macTable, payload)


    prefix, topic_name, suffix, *rest=topic.split('/')



    ### -----------------------------------------------
    ### skip some topics
    ### -----------------------------------------------
    if prefix == 'cmnd' or topic_name in ['tasmotas']:
        gv.logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return


    ### -----------------------------------------------
    ### create device object if not exists
    ### -----------------------------------------------
    if not topic_name in gv.devices:
        gv.logger.info('creating device: %s', topic_name)
        gv.devices[topic_name]=TasmotaClass(gVars=gv, device_name=topic_name)
        refreshDeviceData(topic_name=topic_name, deviceObj=gv.devices[topic_name], mqttClient_CB=mqttClient_CB)

    deviceObj=gv.devices[topic_name]

        ### -----------------------------------------------
        ### comandi derivanti da altre applicazioni per ottenere info
        ### da inviare a telegram group
        ### -----------------------------------------------
    if prefix=='LnTelegram':
        tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, payload=payload)
        return


    if not isinstance(payload, (benedict, dict)):
        gv.logger.warning('%s: skipping payload: %s - %s', topic_name, type(payload), payload)
        return


    ### --------------------------
    ### Process topic
    ### payload must be LnDict()
    ### --------------------------

    ### dati che arrivano direttamente da tasmota
    if prefix=='stat':
        if suffix=='POWER': ### payload is string
            ''' skip perchè prendiamo il topic con json payload 'stat/xxxx/RESULT {"POWER": "OFF"}' '''
            pass

        ### incude tutti gli STATUSx
        elif suffix.startswith('STATUS'):
            deviceObj.updateDevice(key_path='STATUS', data=payload, writeOnFile=True)

        ### in caso di RESULT dobbiamo analizzare il payload
        elif suffix=='RESULT':
            power_key=payload.in_key(in_str='POWER', first_match=True)
            pulsetime_key=payload.in_key(in_str='PulseTime', first_match=True)
            timer_key=payload.in_key(in_str='Timer', first_match=True)
            
            ### action indica se dobbiamo inviare un messaggio a telegram
            action=None

            if power_key:
                deviceObj.updateDevice(key_path=None, data=payload, writeOnFile=True)
                action='power_in_payload'

            ### Tested
            elif pulsetime_key:
                deviceObj.updateLoreto_PulseTime(key_name=pulsetime_key, data=payload)
                action='pulsetime_in_payload'

            elif 'PowerOnState' in payload:
                action='poweronstate_in_payload'

            elif 'Timers' in payload: ### full timers display
                deviceObj.updateDevice(key_path="TIMERS", data=payload, writeOnFile=True)
                action='timers_in_payload'

            elif timer_key and timer_key != 'Timers': ### single timer display
                deviceObj.updateDevice(key_path=f"TIMERS", data=payload, writeOnFile=True)
                action='single_timer_in_payload'


            elif 'SSId1' in payload:
                deviceObj.updateLoreto_SSID(data=payload)
                action='ssid_in_payload'

            elif 'IPAddress1' in payload:
                action='ipaddress_in_payload'

            ### process data
            if action:
                gv.logger.info('%s: %s', topic_name, action)
                tgNotify.in_payload_notify(deviceObj=deviceObj, topic_name=topic_name, action=action, payload=payload)

    ### Tested
    elif prefix=='tele':

        if suffix=='STATE':
            deviceObj.updateDevice(key_path="STATE", data=payload, writeOnFile=True)

        elif suffix=='LWT':
            deviceObj.updateDevice(key_path="LWT", data=payload, writeOnFile=True)

        elif suffix=='HASS_STATE':
            pass

    elif prefix=='tasmota':
        if suffix in ['sensors', 'config']:
            # print(type(payload), isinstance(payload, benedict))
            # import pdb; pdb.set_trace(); pass # by Loreto
            deviceObj.updateDevice(key_path="Config", data=payload, writeOnFile=True)

    else:
        gv.logger.warning("topic: %s not managed - payload: %s", topic, payload)


