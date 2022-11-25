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
import json, yaml
import signal

from LnDict import LoretoDict
import SendTelegramMessage as STM

import Tasmota_Formatter as tasmotaFormatter
import Telegram_Notification as tgNotify




def setup(my_logger):
    global logger, devices, macTable
    logger=my_logger
    devices=LoretoDict()
    macTable=LoretoDict()
    # startTime=time.time()
    # notification_timer_OLD=time.time()
    # notification_timer_OLD={}

    tasmotaFormatter.setup(my_logger=logger)
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







def getRelayNames(device: dict) -> list:
    ### capture relay friendlyNames
    fn=device['sensors.fn']
    if fn:
        friendlyNames=[x for x in fn if (x != '' and x != None)]
        return friendlyNames
    else:
        return []










def sendStatus():
    logger.notify("Sending summary to Telegram")
    for topic_name in devices.keys():
        logger.notify("Sending summary for %s to Telegram", topic_name)
        tgNotify.telegram_notify(topic=f'LnCmnd/{topic_name}/summary', payload=None, devices=devices)






################################################
#----------------------------------------------
################################################
def refreshDeviceData(topic_name: str, mqttClient_CB):
    # global notification_timer_OLD

    # notification_timer_OLD[topic_name]=time.time()
    _commands='state; power; status 0; timers; pulsetime; topic; teleperiod 30; SetOption26 1'
    result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', _commands, qos=0, retain=False)



################################################
### create entry for device name
################################################
def createDeviceEntry(topic_name):
    runtime_dir=os.environ.get('ln_RUNTIME_DIR')
    filename=f"{runtime_dir}/mqtt_monitor/{topic_name}.json"

    if os.path.exists(filename) and os.stat(filename).st_size>0:
        with open(filename, 'r') as fin:
            device=json.load(fin)
    else:
        # device={"Loreto": {"file_out": filename}}
        base_device=f"""
            Loreto:
                file_out: {filename}
                notification_timer: 0
                last_update: None
                device_name: {topic_name}
                topic_name:  {topic_name}
                modello:
                firmware:
                mac1:
                POWER1: N/A
                POWER2: N/A
                Mac: N/A
                IPAddress: N/A
                Gateway: N/A
                Wifi: {dict()}
                relays:         [1, 0, 0, 0, 0, 0, 0, 0 ]
                friendly_names:  ["Relay1", "Relay2", "Relay3", "Relay4", "Relay5", "Relay6", "Relay7", "Relay8"]
                PulseTime:
                    "Set":       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
                    "Remaining": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]

        """

        device=yaml.load(base_device, Loader=yaml.SafeLoader)

    device['notification_timer']=time.time() # azzeriamo comuqnue il timer


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

    ### skip some topics
    if prefix == 'cmnd' or topic_name in ['tasmotas']:
        logger.warning('skipping topic: %s [in attesa di capire meglio come sfruttarlo]', topic)
        return


    ### create device dictionary entry if not exists
    if not topic_name in devices:
        devices[topic_name]=LoretoDict(createDeviceEntry(topic_name))
        refreshDeviceData(topic_name, mqttClient_CB)


    ### dictionary del device
    device=devices[topic_name]
    _loreto=device['Loreto']
    _nRelays=len( [x for x in _loreto['relays'] if x == 1] )
    friendlyNames=[x for x in _loreto['friendly_names'] if (x != '' and x != None)]

    if not payload:
        return
    elif isinstance(payload, dict):
        payload=LoretoDict(payload)

    _topic=f'{prefix}.{suffix}'



    ### --------------------------
    ### Process topic
    ### --------------------------
    fUPDATE_device=True # default

    if prefix=='LnCmnd':
        # telegram_notify(topic=topic, payload=payload, device=device)
        tgNotify.telegram_notify(topic=topic, payload=payload, devices=devices)

    elif prefix == 'stat':

        ### Tested
        if suffix=='STATUS5':
            _ptr=payload['StatusNET']
            _loreto['IPAddress']=_ptr['IPAddress']
            _loreto['Mac']=_ptr['Mac']
            _loreto['Gateway']=_ptr['Gateway']
            _loreto['DNSServer1']=_ptr['DNSServer1']
            _loreto['DNSServer2']=_ptr['DNSServer2']

        ### Tested
        elif suffix=='STATUS10':
            _loreto['last_update']=payload['StatusSNS.Time']

        ### Tested
        elif suffix=='STATUS11':
            _ptr=payload['StatusSTS']
            _loreto['last_update']=_ptr['Time']
            _loreto['Wifi']=_ptr['Wifi']
            for rl in range(1, _nRelays+1):
                key=f'POWER{rl}'
                _loreto[key]=_ptr[key]
                fn=friendlyNames[rl-1]
                _loreto[fn]=_ptr[key]



        elif suffix.startswith('STATUS'):
            pass

        elif suffix=='POWER':
            fUPDATE_device=False
            ''' skip perchè prendiamo il topic con dict payload 'stat/xxxx/RESULT {"POWER": "OFF"}'
            '''

        elif suffix=='RESULT' and payload:
            # per evitare di modificare il topic per updateDevice()
            work_topic=None

            ### Tested
            if payload.key_startswith('POWER'):
                if len(payload.keys())==1:
                    work_topic=f'LnCmnd/{topic_name}/power_in_payload'
                    key=payload.in_key(pattern='POWER')
                    if key:
                        _loreto[key]=payload[key]

            ### Tested
            elif 'Timers' in payload:
                work_topic=f'LnCmnd/{topic_name}/timers_in_payload'

            ### Tested
            elif 'PulseTime' in payload:
                work_topic=f'LnCmnd/{topic_name}/pulsetime_in_payload'
                _loreto['PulseTime'].update(payload['PulseTime'])

            ### Tested
            elif 'SSId1' in payload:
                import pdb; pdb.set_trace(); pass # by Loreto
                work_topic=f'LnCmnd/{topic_name}/ssid_in_payload'
                _loreto['SSID']=payload

            ### process data
            if work_topic:
                # telegram_notify(topic=work_topic, payload=payload, device=device)
                tgNotify.telegram_notify(topic=work_topic, payload=payload, devices=devices)
                fUPDATE_device=True

    ### Tested
    elif prefix=='tele' and suffix=='STATE':
        _loreto['last_update']=payload['Time']
        _loreto['Wifi']=payload['Wifi']
        for rl in range(1, _nRelays+1):
            key=f'POWER{rl}'
            _loreto[key]=payload[key]
            fn=friendlyNames[rl-1]
            _loreto[fn]=payload[key]


    elif prefix=='tasmota' and suffix=='sensors':
        ### Tested
        if 'sn' in payload:
            _loreto['last_update']=payload['sn.Time']

        ### Tested
        elif 'rl' in payload:
            _loreto['relays']=[x for x in payload['rl'] if x == 1]
            _loreto['friendly_names']=[x for x in payload['fn'] if (x != '' and x != None)]

            _loreto['ip_address']=payload['ip']
            _loreto['device_name']=payload['dn']
            _loreto['topic_name']=payload['t']
            _loreto['modello']=payload['md']
            _loreto['firmware']=payload['sw']
            _loreto['mac1']=payload['mac'] # formato senza punti ... da modificare

    elif _topic in ['tele.LWT', 'tele.HASS_STATE', 'shellies.ext_temperatures', 'tasmota.sensors']:
        pass

    else:
        logger.warning("topic: %s not managed - payload: %s", topic, payload)
        fUPDATE_device=True



    if fUPDATE_device:
        updateDevice(topic=topic, payload=payload, writeFile=True)

