#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)

import threading
from queue import Queue
import time
import json
import signal

from LnDict import LoretoDict
import SendTelegramMessage as STM

import Tasmota_Formatter as tasmotaFormatter




def setup(my_logger):
    global logger, devices, macTable, startTime
    logger=my_logger
    devices=LoretoDict()
    macTable=LoretoDict()
    startTime=time.time()
    tasmotaFormatter.setup(my_logger=logger)






def sendStatus():
    logger.notify("Sending summary to Telegram")
    for topic_name in devices.keys():
        logger.notify("Sending summary for %s to Telegram", topic_name)
        telegram_notify(topic=f'LnCmnd/{topic_name}/summary', payload=None)



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







def getRelayNames(device: dict) -> list:
    ### capture relay friendlyNames
    fn=device.getkp('sensors.fn')
    if fn:
        friendlyNames=[x for x in fn if (x != '' and x != None)]
        return friendlyNames
    else:
        return []





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
def telegram_notify(topic: str, payload: (dict, str)=None, device: dict=None):
    logger.info('processing topic %s for telegram message', topic)
    _,  topic_name, suffix=topic.split('/')

    _dict=LoretoDict()

    if not device and topic_name in devices:
        device=devices[topic_name]

    # import pdb; pdb.set_trace(); pass # by Loreto
    if 'STATE' in device and 'sensors' in device:
        relayNames=getRelayNames(device)

        if suffix=='summary':
            _dict.update(tasmotaFormatter.deviceInfo(data=device))
            _dict['Wifi']=tasmotaFormatter.wifi(data=device)

            for index, name in enumerate(relayNames):
                pt_value, pt_remaining=tasmotaFormatter.getPulseTime(data=device, relayNr=index)
                relay_status=tasmotaFormatter.retrieveRelayStatus(data=device, relayNr=index+1)
                timers_status=tasmotaFormatter.timers(data=device, outputRelay=index+1)

                _dict.setkp(f"RL_{name}.Pulsetime", value=pt_value, create=True)
                _dict.setkp(f"RL_{name}.Remaining", value=pt_remaining, create=True)
                _dict.setkp(f"RL_{name}.Status", value=relay_status, create=True)
                _dict.setkp(f"RL_{name}.Timers", value=timers_status, create=True)

        elif suffix=='timers_in_payload':
            _dict['Timers']=tasmotaFormatter.timers(data=payload, outputRelay=0)


        elif suffix=='power_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
            # import pdb; pdb.set_trace(); pass # by Loreto
            for index, name in enumerate(relayNames):
                relay_status=tasmotaFormatter.retrieveRelayStatus(data=device, new_data=payload, relayNr=index+1)
                _dict.setkp(f"RL_{name}.Status", value=relay_status, create=True)

        elif suffix=='pulsetime_in_payload':     # payload dovrebbe contenere qualcosa tipo: {"POWER1":"OFF"}
            for index, name in enumerate(relayNames):
                pt_value, pt_remaining=tasmotaFormatter.getPulseTime(data=payload, relayNr=index)
                _dict.setkp(f"RL_{name}.Pulsetime", value=pt_value, create=True)
                _dict.setkp(f"RL_{name}.Remaining", value=pt_remaining, create=True)

        else:
            return

    else:
        logger.warning('%s - non discovered too', topic_name)
        # _dict['relays']="N/A"

    fSLEEP=(time.time()-startTime)>10 # ignore first messages during progrram startup

    if _dict and fSLEEP:
        tg_msg=LoretoDict({topic_name: _dict })
        logger.warning('sending telegram message: %s', tg_msg)
        STM.sendMsg(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), my_logger=logger)














#----------------------------------------------
def refreshDeviceData(topic_name: str, mqttClient_CB):
    _commands='power; status 0; timers; pulsetime; topic; teleperiod 30; SetOption26 1'
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', _commands, qos=0, retain=False)
    '''
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'power', qos=0, retain=False)
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'status 0', qos=0, retain=False)
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'timers', qos=0, retain=False)
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'pulsetime', qos=0, retain=False)
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'topic', qos=0, retain=False)
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'teleperiod 30', qos=0, retain=False)
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'SetOption26 1', qos=0, retain=False) # set power1 instead of power
    '''
#----------------------------------------------


### create entry for device name
def createDeviceEntry(topic_name):
    runtime_dir=os.environ.get('ln_RUNTIME_DIR')
    filename=f"{runtime_dir}/mqtt_monitor/{topic_name}.json"
    if os.path.exists(filename) and os.stat(filename).st_size>0:
        with open(filename, 'r') as fin:
            device=json.load(fin)
    else:
        device={"Loreto": {"file_out": filename}}

    return device


################################################
### add/update payload to device
### crea una entry con il suffix
################################################
def updateDevice(topic: str, payload: dict, writeFile=True):
    prefix, topic_name, suffix, *rest=topic.split('/')
    device=devices[topic_name]

    if suffix in device and isinstance(payload, dict) and isinstance(device[suffix], dict):
        try:
            device[suffix].update(payload)
        except (AttributeError) as exc:
            print(str(exc))
            print("topic:        ",  topic)
            print("payload:      ",  payload)
            print("suffix:       ",  suffix)
            print("device[suffix]:", device[suffix])
            os.kill(int(os.getpid()), signal.SIGTERM)
    else:
        device[suffix]=payload

    fileout=device['Loreto.file_out']
    if writeFile and fileout:
        logger.info('updating file: %s', fileout)
        device.toJsonFile(filename=fileout, replace=True)








#########################################################
# In tasmota abbiamo:
#  Device name:     Configuration->Other  nome del device che compare sulla home
#  Friendly name:   Configuration->Other  nome del/dei realys contenuti nel dispositivo
#  Topic name:      Configuration->MQTT   nome del topic con cui si presenta nel Broker MQTT
#  Per comodità cerco di utilizzare il topic_name==Device_name
#########################################################
def process(topic, payload, mqttClient_CB):
    logger.info('processing topic: %s', topic)

    """ topic='tasmota/discovery/DC4F22D3B32F/sensors'
        cambiare il topic attraverso il MAC
    """
    if topic.startswith("tasmota/discovery"): ### viene rilasciato automaticamente da tasmota
        topic=tasmota_discovery_modify_topic(topic, macTable, payload)

    prefix, topic_name, suffix, *rest=topic.split('/')
    if prefix == 'cmnd':
        logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return

    ### comando per tutti, catturiamo solo i risultati
    if topic_name in ['tasmotas']:
        logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return

    ### create device dictionary entry if not exists
    if not topic_name in devices:
        devices[topic_name]=LoretoDict(createDeviceEntry(topic_name))
        refreshDeviceData(topic_name, mqttClient_CB)


    ### dictionary del device
    device=devices[topic_name]
    if isinstance(payload, dict):
        payload=LoretoDict(payload)

    _topic=f'{prefix}.{suffix}'




    ### --------------------------
    ### Process topic
    ### --------------------------
    fUPDATE_device=False # default

    if prefix=='LnCmnd':
        telegram_notify(topic=topic, payload=payload, device=device)

    elif prefix == 'stat' and suffix.startswith('STATUS'):
        fUPDATE_device=True

    elif _topic=='stat.POWER':
        pass
        ''' skip perchè prendiamo il topic con dict payload 'stat/xxxx/RESULT {"POWER": "OFF"}'
        '''

    elif prefix=='stat' and suffix=='RESULT' and payload:
        # per evitare di modifiacre il topic per updateDevice()
        lncmnd_topic=None

        if payload.key_startswith('POWER'):
            lncmnd_topic=f'LnCmnd/{topic_name}/power_in_payload'

        elif 'Timers' in payload:
            lncmnd_topic=f'LnCmnd/{topic_name}/timers_in_payload'

        elif 'PulseTime' in payload:
            lncmnd_topic=f'LnCmnd/{topic_name}/pulsetime_in_payload'

        ### process data
        if lncmnd_topic:
            telegram_notify(topic=lncmnd_topic, payload=payload, device=device)
            fUPDATE_device=True


    elif _topic in ['tele.STATE', 'tele.LWT', 'tele.HASS_STATE', 'shellies.ext_temperatures', 'tasmota.sensors']:
        fUPDATE_device=True

    else:
        logger.warning("topic: %s not managed", topic)
        logger.warning(payload)



    if fUPDATE_device:
        updateDevice(topic=topic, payload=payload, writeFile=True)

