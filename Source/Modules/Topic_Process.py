#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 10-12-2022 08.47.12

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)
from types import SimpleNamespace
import threading
from queue import Queue
import time
import json, yaml
import signal

from LoretoDict import LnDict
import SendTelegramMessage as STM

# import Tasmota_Formatter as tasmotaFormatter
import Telegram_Notification as tgNotify

from Tasmota_Class import TasmotaClass





def setup(gVars: SimpleNamespace):
    global gv, logger, devices, macTable
    gv=gVars
    logger=gv.logger
    devices=dict()
    macTable=dict()

    tgNotify.setup(my_logger=logger)





#####################################################################
# process topic name and paylod data to find_out topic_name,
# topic='tasmota/discovery/DC4F22BE4445/sensors'
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
    _tasmota, _discovery, _mac,  _sensors, *rest=topic.split('/')

    topic=None
    if _mac in mac_table:
        topic_name=macTable[_mac]
        topic=f'tasmota/{topic_name}/sensors'


    mac=payload.get('mac')
    topic_name=payload.get('t')

    if mac and topic_name:
        mac_table[mac]=topic_name # add to table
        topic=f'tasmota/{topic_name}/sensors'

    return topic






##########################################################
# Invia un summary status per tutti i deivce
##########################################################
def sendStatus():
    logger.notify("Sending summary to Telegram")
    for topic_name in devices.keys():
        logger.notify("Sending summary for %s to Telegram", topic_name)
        tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, action=action, payload=payload)






################################################
#-
################################################
def refreshDeviceData(topic_name: str, deviceObj, mqttClient_CB):
    deviceObj.telegramNotification(seconds=20) # temoporary stop to telegram notification
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
    logger.info('processing topic: %s', topic)


    #--------------------------------------
    # analisi del topic_name, del device e del payload
    #--------------------------------------

    ### viene rilasciato automaticamente da tasmota
    if topic.startswith("tasmota/discovery"):
        """ topic='tasmota/discovery/DC4F22D3B32F/sensors'
            cambiare il topic attraverso il MAC """
        topic=tasmota_discovery_modify_topic(topic, macTable, payload)


    prefix, topic_name, suffix, *rest=topic.split('/')

    ### skip some topics
    if prefix == 'cmnd' or topic_name in ['tasmotas']:
        logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return


    ### create device dictionary entry if not exists
    if not topic_name in devices:
        logger.info('creating device: %s', topic_name)
        devices[topic_name]=TasmotaClass(device_name=topic_name, runtime_dir=gv.mqttmonitor_runtime_dir, logger=logger)
        refreshDeviceData(topic_name=topic_name, deviceObj=devices[topic_name], mqttClient_CB=mqttClient_CB)

    if not payload:
        logger.warning('%s: no payload', topic_name)
        return

    elif isinstance(payload, dict):
        payload=LnDict(payload)

    logger.info('%s: processing', topic)
    logger.info('   payload: %s', payload)




    ### device object
    deviceObj=devices[topic_name]
    _topic=f'{prefix}.{suffix}'

    prefix_suffix=f'{prefix}.{suffix}'



    ### --------------------------
    ### Process topic
    ### --------------------------
    fUPDATE_device_file=True # default



    ### comandi derivanti da applicazioni per ottenere un mix di dati
    if prefix=='LnCmnd':
        tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, action=suffix, payload=payload)


    ### dati che arrivano direttamente da tasmota
    elif prefix=='stat':
        if suffix=='POWER':
            fUPDATE_device_file=False
            ''' skip perchè prendiamo il topic con json payload 'stat/xxxx/RESULT {"POWER": "OFF"}' '''
            _payload={}

        ### Tested
        elif suffix.startswith('STATUS'):
            ''' incude tutti gli STATUSx '''
            deviceObj.updateDevice(main_key_path=f"{topic_name}", data=payload, writeFile=True)


        ### in caso di RESULT dobbiamo analizzare il payload
        elif suffix=='RESULT' and payload:
            action=None

            ### Tested
            if payload.key_startswith('POWER'):
                deviceObj.updateLoreto_POWER(data=payload)
                deviceObj.updateDevice(main_key_path=f"Loreto", data=payload, writeFile=True)
                action='power_in_payload'

            elif 'PowerOnState' in payload:
                action='poweronstate_in_payload'

            ### Tested
            elif 'Timers' in payload:
                deviceObj.updateDevice(main_key_path=f"{topic_name}.TIMERS", data=payload, writeFile=True)
                action='timers_in_payload'

            ### Tested
            elif 'PulseTime' in payload:
                deviceObj.updateLoreto_PulseTime(data=payload)
                action='pulsetime_in_payload'

            ### Tested
            elif 'SSId1' in payload:
                deviceObj.updateLoreto_SSID(data=payload)
                action='ssid_in_payload'

            elif 'IPAddress1' in payload:
                action='ipaddress_in_payload'

            ### process data
            if action:
                tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, action=action, payload=payload)

    ### Tested
    elif prefix=='tele':

        if suffix=='STATE':
            deviceObj.updateLoreto_STATE(data=payload)
            deviceObj.updateLoreto_POWER(data=payload)
            deviceObj.updateDevice(main_key_path=f"{topic_name}.STATE", data=payload, writeFile=True)

        elif suffix=='LWT':
            deviceObj.updateDevice(main_key_path=f"{topic_name}.LWT", data=payload, writeFile=True)

        elif suffix=='HASS_STATE':
            pass

    elif prefix=='shelliesx':
        if suffix=='ext_temperatures':
            pass


    elif prefix=='tasmota' and suffix=='sensors':
        ### Tested
        if 'sn' in payload:
            deviceObj.updateLoreto_SensorsSN(data=payload)
            deviceObj.updateDevice(main_key_path=f"{topic_name}.Sensors", data=payload, writeFile=True)

        ### Tested
        elif 'rl' in payload:
            deviceObj.updateLoreto_SensorsRL(data=payload)
            deviceObj.updateDevice(main_key_path=f"{topic_name}.Sensors", data=payload, writeFile=True)


    else:
        logger.warning("topic: %s not managed - payload: %s", topic, payload)


    deviceObj.savingDataOnFile()
