#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 03-12-2022 09.00.20

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)

import threading
from queue import Queue
import time
import json, yaml
import signal

from LoretoDict import LnDict
import SendTelegramMessage as STM

# import Tasmota_Formatter as tasmotaFormatter
import Telegram_Notification_V1_0 as tgNotify

from Tasmota_Class import TasmotaClass





def setup(my_logger):
    global logger, devices, macTable
    logger=my_logger
    devices=LnDict()
    macTable=LnDict()

    # tasmotaFormatter.setup(my_logger=logger)
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
        tgNotify.telegram_notify(deviceObj=devices[topic_name], topic=f'LnCmnd/{topic_name}/summary', payload=None)






################################################
#----------------------------------------------
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
# In tasmota abbiamo:
#  Device name:     Configuration->Other  nome del device che compare sulla home
#  Friendly name:   Configuration->Other  nome del/dei realys contenuti nel dispositivo
#  Topic name:      Configuration->MQTT   nome del topic con cui si presenta nel Broker MQTT
#  Per comodità cerco di utilizzare il topic_name==Device_name
#########################################################
def process(topic, payload, mqttClient_CB):
    logger.info('processing topic: %s', topic)
    runtime_dir=os.environ.get('ln_RUNTIME_DIR')



    """ topic='tasmota/discovery/DC4F22D3B32F/sensors'
        cambiare il topic attraverso il MAC
    """
    if topic.startswith("tasmota/discovery"): ### viene rilasciato automaticamente da tasmota
        topic=tasmota_discovery_modify_topic(topic, macTable, payload)


    prefix, topic_name, suffix, *rest=topic.split('/')

    ### skip some topics
    if prefix == 'cmnd' or topic_name in ['tasmotas']:
        logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return


    ### create device dictionary entry if not exists
    if not topic_name in devices:
        logger.info('creating device: %s', topic_name)
        devices[topic_name]=TasmotaClass(device_name=topic_name, runtime_dir=runtime_dir, logger=logger)
        refreshDeviceData(topic_name=topic_name, deviceObj=devices[topic_name], mqttClient_CB=mqttClient_CB)

    if not payload:
        logger.warning('%s: no payload', topic_name)
        return

    elif isinstance(payload, dict):
        payload=LnDict(payload)
    logger.info('   payload: %s', payload)


    ### device object
    deviceObj=devices[topic_name]
    friendlyNames=deviceObj.friendlyNames()
    _topic=f'{prefix}.{suffix}'

    prefix_suffix=f'{prefix}.{suffix}'


    deviceObj.updateGeneric(suffix=suffix, data=payload, writeFile=False)

    ### --------------------------
    ### Process topic
    ### --------------------------
    fUPDATE_device_file=True # default

    logger.info('%s: processing', topic)


    if prefix=='LnCmnd':
        tgNotify.telegram_notify(deviceObj=deviceObj, topic=topic, payload=payload)


    elif prefix=='stat':
        if suffix=='POWER':
            fUPDATE_device_file=False
            ''' skip perchè prendiamo il topic con json payload 'stat/xxxx/RESULT {"POWER": "OFF"}' '''

        ### Tested
        elif suffix=='STATUS5':
            deviceObj.updateSTATUS5(data=payload)

        ### Tested
        elif suffix=='STATUS10':
            deviceObj.updateSTATUS10(data=payload)

        ### Tested
        elif suffix=='STATUS11':
            if isinstance(payload, dict): # a volte arriva sbagliato come nell'AreazioneSuperiore
                deviceObj.updateSTATUS11(data=payload)
            else:
                self.logger.error("%s - ERRORE nello STATUS11: %s", topic_name, payload)


        elif suffix=='RESULT' and payload:
            lncmnd_topic=None

            ### Tested
            if payload.key_startswith('POWER'):
                deviceObj.updatePOWER(data=payload)
                lncmnd_topic=f'LnCmnd/{topic_name}/power_in_payload'

            ### Tested
            elif 'Timers' in payload:
                deviceObj.updateTIMERS(data=payload)
                lncmnd_topic=f'LnCmnd/{topic_name}/timers_in_payload'

            ### Tested
            elif 'PulseTime' in payload:
                deviceObj.updatePulseTime(data=payload)
                lncmnd_topic=f'LnCmnd/{topic_name}/pulsetime_in_payload'

            ### Tested
            elif 'SSId1' in payload:
                deviceObj.updateSSID(data=payload)
                lncmnd_topic=f'LnCmnd/{topic_name}/ssid_in_payload'

            ### process data
            if lncmnd_topic:
                tgNotify.telegram_notify(deviceObj=deviceObj, topic=lncmnd_topic, payload=payload)

    ### Tested
    elif prefix=='tele':

        if suffix=='STATE':
            deviceObj.updateSTATE(data=payload)


    elif prefix=='shellies':
        if suffix=='ext_temperatures':
            pass


    elif prefix=='tasmota' and suffix=='sensors':
        ### Tested
        if 'sn' in payload:
            deviceObj.updateSensorsSN(data=payload)

        ### Tested
        elif 'rl' in payload:
            deviceObj.updateSensorsRL(data=payload)

    elif _topic in ['tele.LWT', 'tele.HASS_STATE', 'shellies.ext_temperatures', 'tasmota.sensors']:
        pass

    else:
        logger.warning("topic: %s not managed - payload: %s", topic, payload)



    if fUPDATE_device_file:
        deviceObj.updateGeneric(suffix=suffix, data=payload, writeFile=True)

