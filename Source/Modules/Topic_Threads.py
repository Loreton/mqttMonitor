#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 01-12-2022 08.40.16

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
from LoretoDict import LnDict
from TelegramMessage import telegramSend


import threading
from queue import Queue
import time

import Tasmota_Formatter as tasmotaFmt


# es http://stackoverflow.com/questions/10525185/python-threading-how-do-i-lock-a-thread

# splitted INIT con lo start
class myThread(threading.Thread):
    def __init__(self, lock, argsFunc=(), name=None, daemon=True, inputQueue=None, outputQueue=None, start=False):
        threading.Thread.__init__(self, args=argsFunc)
        self.name    = name
        self.daemon  = daemon   # True... die when main die
        self.inputQ  = inputQueue
        self.outputQ = outputQueue
        self.lock    = lock
        if start:
            self.start_my_thread()

    def start_my_thread(self, lock=None, name=None, daemon=True, inputQueue=None, outputQueue=None ):
        if name        : self.name    = name
        if daemon      : self.daemon  = daemon    # True... die when main die
        if inputQueue  : self.inputQ  = inputQueue
        if outputQueue : self.outputQ = outputQueue
        if lock        : self.lock    = lock
        self.start()


    # ------------------------------------------------------------------
    # - funzione che scoda il messaggio e lo manda in esecuzione
    # - chiude quando il main chiude
    # -  Es.:
    # -      functionName = {'funcPTR': ptrFunctions[index]}
    # -      ... oppure
    # -      functionName = {'funcName': ptrFunctions[index]}
    # -
    # -      parameters   = {'parm01': 'pippo', 'parm02': 'pluto'}
    # -      myQueue.put([functionName, **parameters])
    # -------------------------------------------------------------------
    def run(self):
        while True:  # while main thread is alive and all daemons died
            functionPtr, funcArgs=self.inputQ.get()
            logger.trace('')
            logger.trace('---------- ThreaderExecutor --------------')
            logger.trace("function name: %s", functionPtr.__name__)
            logger.trace("function args: %s", funcArgs)

            try:
                result = functionPtr(**funcArgs)
            except:
                result = -1

            if self.outputQ:
                self.outputQ.put([functionPtr.__name__, result])
            '''
                You don't have to call task_done() unless you use Queue.join() function.
                Queue.join() blocks until all items in the queue have been gotten and processed.
            self.inputQ.task_done()
            '''







def setup(my_logger):
    global logger, devices, myThreads, inputQ, resultQ, macTable
    logger=my_logger
    devices=LnDict()
    macTable=LnDict()
    myThreads = []

    # -------------------------------------------------------
    # - Facciamo partire i threads
    # -------------------------------------------------------
    max_threads=5
    inputQ = Queue()
    resultQ = Queue()
    resultQ = None
    print_lock = threading.Lock()
    autostart=True

    ### initialize Threads
    for index in range(1, max_threads+1):
        t = myThread(lock=print_lock, name=f'mqtt_monitor{index:02}', inputQueue=inputQ, outputQueue=resultQ, start=autostart)
        myThreads.append(t)

    # start manually
    if not autostart:
        for t in myThreads:
            t.start_my_threads()







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
def topic_tasmota_discovery(topic, mac_table, payload):
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












######################################################
# process topic name and paylod data to findout query,
# topic='LnCmnd/telegram/query'
# payload={"topic_name": "Tasmota_002", "query": "status"} # importante DQ
######################################################
def from_telegram_command(topic: str, payload: dict, device: dict):
    _,  topic_name, _query=topic.split('/')

    if isinstance(payload, dict):
        query=payload['query']
    else:
        query=payload.strip()

    qdata=LnDict()
    if query=='status':
        qdata.update(tasmotaFmt.deviceInfo(device))
        qdata['Wifi']=tasmotaFmt.wifi(device)
        qdata['relays']=tasmotaFmt.relayStatus(device)
    elif query=='power':
        qdata.update(tasmotaFmt.deviceInfo(device))
        qdata['relays']=tasmotaFmt.relayStatus(device)
    else:
        return


    tg_msg=LnDict({topic_name: qdata })
    telegramSend(group_name=topic_name, message=tg_msg.to_yaml(sort_keys=False), logger=logger)














######################################################
# process payload data,
# insert it to device dictionary
# an save all to json file
######################################################
def payload_worker(topic, payload, device, fUPDATE_file: bool=False):
    logger.notify("%s - start payload worker", topic)
    prefix, topic_name, suffix, *rest=topic.split('/')
    loretoPtr=device['Loreto']


    if not suffix in device:
        device[suffix]=payload
    else:
        device[suffix].update(payload)

    if prefix == 'tele' and suffix=='STATE':
        pass
    elif prefix == 'tele' and suffix=='HASS_STATE':
        pass
    elif prefix == 'stat' and suffix.startswith('STATUS'):
        pass
    elif prefix == 'stat' and suffix=='RESULT':
        if payload.key_startswith('POWER'):
            time.sleep(5)
            topic=f'LnCmnd/{topic_name}/query'
            from_telegram_command(topic=topic, payload='power', device=device)

    elif prefix == 'shellies' and suffix=='ext_temperatures':
        pass
    elif prefix == 'tasmota' and suffix=='sensors':
        pass

    # topic: stat/VescoviNew/RESULT payload: {'POWER1': 'ON'}
    elif prefix == 'stat' and suffix=='RESULT':
        pass

    # elif prefix == 'LnCmnd' and suffix=='query':
    #     fUPDATE_file=False
    #     time.sleep(5)
    #     from_telegram_command(topic=topic, payload=payload, device=device)

    else:
        fUPDATE_file=False
        logger.warning("topic: %s not managed", topic)
        logger.notify(payload)

    if fUPDATE_file:
        device.toJsonFile(file_out=loretoPtr["file_out"], replace=True)

    logger.notify("%s - end payload worker", topic)
    return 0





#########################################################
# In tasmota abbiamo:
#  Device name: Configuration->Other
#          nome del device che compare sulla home
#  Friendly name: Configuration->Other
#          nome del/dei realys contenuti nel dispositivo
#  Topic name: Configuration->MQTT
#          nome del topic con cui si presenta nel Broker MQTT
#  Per comodità cerco di utilizzare il topic_name==Device_name
#########################################################
def process(topic, payload, mqttClient_CB):
    #----------------------------------------------
    def refreshData(topic_name: str, mqttClient_CB):
        result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'power', qos=0, retain=False)
        result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'status 0', qos=0, retain=False)
        result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'timers', qos=0, retain=False)
        result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'pulsetime', qos=0, retain=False)
        result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'topic', qos=0, retain=False)
        result=mqttClient_CB.publish(f'cmnd/{topic_name}/backlog', 'teleperiod 30', qos=0, retain=False)
    #----------------------------------------------
    if isinstance(payload, dict):
        payload=LnDict(payload)

    """ topic='tasmota/discovery/DC4F22D3B32F/sensors'
        cambiare il topic attraverso il MAC
    """
    if topic.startswith("tasmota/discovery"):
        topic=topic_tasmota_discovery(topic, macTable, payload)

    prefix, topic_name, suffix, *rest=topic.split('/')

    if topic_name in devices:
        device=devices[topic_name]

        if prefix == 'LnCmnd' and suffix=='query':
            refreshData(topic_name, mqttClient_CB)
            time.sleep(5)
            from_telegram_command(topic=topic, payload=payload, device=device)
            return

        ### prepare for thread
        functionPtr=payload_worker
        funcArgs={'topic': topic, 'payload': payload, 'device': device, 'fUPDATE_file': True}

        logger.notify('-'*10)
        logger.notify("     %s - starting Thread", topic_name)
        logger.notify("     function: %s", functionPtr.__name__)
        logger.trace( "     args:     %s", funcArgs)
        inputQ.put([functionPtr, funcArgs])

        """
            non attendo risposte... altrimenti:
            while(resultQ.empty() == False):
                result = resultQ.get()
                logger.info("topic_name: %s result: %s", topic_name, result)
        """
        logger.notify('-'*10)

    else:
        ### create entry for device name
        devices[topic_name]=LnDict()
        devices[topic_name]['Loreto']=LnDict()

        devices[topic_name]['Loreto']['file_out']=os.path.expandvars(f"$ln_RUNTIME_DIR/mqtt_monitor/{topic_name}.json")
        if prefix in ['tele', 'stat', 'cmnd', 'LnCmnd']:
            refreshData(topic_name, mqttClient_CB)

