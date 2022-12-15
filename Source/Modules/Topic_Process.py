#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 15-12-2022 16.52.00

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

# from LoretoDict import LnDict
import SendTelegramMessage as STM
from benedict import benedict

# import Tasmota_Formatter as tasmotaFormatter
import Telegram_Notification as tgNotify

from Tasmota_Class import TasmotaClass





def setup(gVars: SimpleNamespace):
    global gv, logger, devices, macTable
    gv=gVars
    logger=gv.logger
    devices=dict()
    macTable=dict()

    # tgNotify.setup(my_logger=logger)





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
        topic_name=macTable[_mac]

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
    logger.notify("Sending summary to Telegram")
    for topic_name in devices.keys():
        logger.notify("Sending summary for %s to Telegram", topic_name)
        tgNotify.telegram_notify(deviceObj=devices[topic_name], topic_name=topic_name, action='summary', payload=None)






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
    logger.info('   payload: %s - %s', type(payload), payload)


    #--------------------------------------
    # analisi del topic_name, del device e del payload
    #--------------------------------------

    ### viene rilasciato automaticamente da tasmota
    if topic.startswith("tasmota/discovery"):
        """ topic='tasmota/discovery/DC4F22D3B32F/sensors'
            topic='tasmota/discovery/DC4F22D3B32F/config'
            cambiare il topic attraverso il MAC """
        topic=tasmota_discovery_modify_topic(topic, macTable, payload)


    prefix, topic_name, suffix, *rest=topic.split('/')



    ### -----------------------------------------------
    ### skip some topics
    ### -----------------------------------------------
    if prefix == 'cmnd' or topic_name in ['tasmotas']:
        logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return


    ### -----------------------------------------------
    ### create device dictionary entry if not exists
    ### -----------------------------------------------
    if not topic_name in devices:
        logger.info('creating device: %s', topic_name)
        devices[topic_name]=TasmotaClass(device_name=topic_name, runtime_dir=gv.mqttmonitor_runtime_dir, logger=logger)
        refreshDeviceData(topic_name=topic_name, deviceObj=devices[topic_name], mqttClient_CB=mqttClient_CB)


    ### -----------------------------------------------
    ### device object
    ### -----------------------------------------------
    deviceObj=devices[topic_name]
    # logger.notify('%s - %s', topic_name, deviceObj.full_device.to_json())
    # logger.notify('     %s', deviceObj.loretoDB.to_json() )
    # logger.notify('     %s', deviceObj.loretoDB['relays'] )
    ### -----------------------------------------------
    ### comandi derivanti da applicazioni per ottenere un mix di dati
    ### -----------------------------------------------
    if prefix=='LnCmnd':
        tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, action=suffix, payload=payload)
        return



    if isinstance(payload, dict):
        payload=benedict(payload)
    else:
        logger.warning('%s: skipping payload: %s - %s', topic_name, type(payload), payload)
        return


    ### --------------------------
    ### Process topic
    ### payload must be LnDict()
    ### --------------------------

    ### dati che arrivano direttamente da tasmota
    if prefix=='stat':
        if suffix=='POWER':
            ''' skip perchè prendiamo il topic con json payload 'stat/xxxx/RESULT {"POWER": "OFF"}' '''
            pass

        ### incude tutti gli STATUSx
        elif suffix.startswith('STATUS'):
            deviceObj.updateDevice(key_path='STATUS', data=payload, writeFile=True)



        ### in caso di RESULT dobbiamo analizzare il payload
        elif suffix=='RESULT':
            power_key=payload.in_key(in_str='POWER', return_first=True)
            pulsetime_key=payload.in_key(in_str='PulseTime', return_first=True)

            action=None

            if power_key:
                deviceObj.updateLoreto_POWER(data=payload)
                deviceObj.updateDevice(key_path=None, data=payload, writeFile=True)
                action='power_in_payload'

            ### Tested
            elif pulsetime_key:
                deviceObj.updateLoreto_PulseTime(key_name=pulsetime_key, data=payload)
                action='pulsetime_in_payload'

            elif 'PowerOnState' in payload:
                action='poweronstate_in_payload'

            elif 'Timers' in payload:
                deviceObj.updateDevice(key_path="TIMERS", data=payload, writeFile=True)
                action='timers_in_payload'


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
            # deviceObj.updateLoreto_STATE(data=payload) # update also Wifi
            # deviceObj.updateLoreto_POWER(data=payload)
            deviceObj.updateDevice(key_path="STATE", data=payload, writeFile=True)

        elif suffix=='LWT':
            deviceObj.updateDevice(key_path="LWT", data=payload, writeFile=True)

        elif suffix=='HASS_STATE':
            pass

    elif prefix=='shelliesx':
        if suffix=='ext_temperatures':
            pass


    elif prefix=='tasmota':
        if suffix in ['sensors', 'config']:
            if suffix == 'sensors':
                pass
                # import pdb; pdb.set_trace(); pass # by Loreto

            deviceObj.updateDevice(key_path="Config", data=payload, writeFile=True)

        '''
        if suffix in ['sensors', 'config']:
            ### Tested
            if 'sn' in payload:
                # deviceObj.updateLoreto_SensorsSN(data=payload)
                deviceObj.updateDevice(key_path="Config.Sensors", data=payload, writeFile=True)

            ### Tested
            elif 'rl' in payload:
                # deviceObj.updateLoreto_SensorsRL(data=payload)
                deviceObj.updateDevice(key_path="Config.Sensors", data=payload, writeFile=True)

        elif suffix=='config':
            deviceObj.updateDevice(key_path="Config.Config", data=payload, writeFile=True)
        '''


    else:
        logger.warning("topic: %s not managed - payload: %s", topic, payload)


    # deviceObj.savingDataOnFile()
