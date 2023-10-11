#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
from types import SimpleNamespace
import random


import  signal
import  yaml, json
from    paho.mqtt import client as mqtt_client
import  uuid
import  time
import  subprocess, shlex
import socket; hostname=socket.gethostname()
from benedict import benedict

from    LnTimer import TimerLN as LnTimer
from    savePidFile import savePidFile

import  Tasmota_Device
import  Shellies_Device
import  LnCmnd_Process as LnCmnd
import  Tasmota_Telegram_Notification as tgNotify
import  TelegramSendMessage as TSM

from Tasmota_Class import TasmotaClass



#######################################################
# Intercetta il Ctrl-C
#######################################################
def signal_handler_Mqtt(signalLevel, frame):
    gv.logger.warning("signalLevel: %s", signalLevel)

    # client.Stop(termination_code=0, msg="signal_handler_Mqtt function") # stop mqtt and return
    gv.client.loop_stop()
    pid=os.getpid()

    if gv.args.systemd:
        print('sono qui')
        gv.logger.warning("MQTT server - Terminating on SIGTERM signalLevel [%s] under systemd control ", signalLevel)
        # threading.Thread(target=shutdown).start()
        os.kill(int(os.getpid()), signal.SIGTERM)
        sys.exit(1)

    elif int(signalLevel)==2:
        print('\n'*5)
        gv.logger.warning("MQTT server - Restarting on SIGINT [ctrl-c] signalLevel [%s]", signalLevel)
        command=f'ps -p {pid} -o args'
        splitted_cmd=shlex.split(command)
        output=subprocess.check_output(splitted_cmd, universal_newlines=True)
        cmd_line=output.split('\n')[1]
        splitted_cmd=shlex.split(cmd_line)
        gv.logger.warning('restarting: %s', splitted_cmd)
        print('\n'*5)
        # time.sleep(2)
        input('Press enter to continue...')
        os.execv(sys.executable, splitted_cmd)
    else:
        gv.logger.warning("MQTT server - Terminating on SIGTERM signalLevel [%s]", signalLevel)
        sys.exit(1)


import signal
signal.signal(signal.SIGINT, signal_handler_Mqtt)



####################################################################
#  This function clears the retained flag by publishing
#  a empty message (msg=””) with the retained flag set.
####################################################################
def clear_retained_topic(client, message):
    _msg=str(message.payload.decode("utf-8"))
    gv.logger.warning('Trying to clear retained on message: %s topic: %s', _msg, message.topic)
    _msg=''
    result=client.publish(message.topic, _msg, qos=0, retain=True)
    gv.logger.warning(result)


####################################################################
#
####################################################################
def connect_mqtt(client_id: str) -> mqtt_client:
    gv.logger.info("Connecting to MQTT Broker: %s", gv.broker)
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            gv.logger.info("Connected to MQTT Broker!")
        else:
            gv.logger.info("Failed to connect, return code %d\n", rc)
            gv.telegramMessage.send_html(group_name=gv.tg_group_name, message=f"Failed to connect to mqtt, return code:{rc}", caller=True) ### markdown dà errore
            os.kill(int(os.getpid()), signal.SIGTERM)
            sys.exit(1)


    def on_disconnect(client, userdata, rc):
        logging.info("disconnecting reason: %s", rc)
        client.loop_stop()
        client.connected_flag=False
        client.disconnect_flag=True


    HIVE_MQ=False
    if HIVE_MQ:
        print('da implemetare')
        sys.exit(1)
    else:
        broker=gv.broker
        auth=dict(broker.auth)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    if auth: client.username_pw_set(**auth)
    rcode=client.connect(broker.url, int(broker.port))

    return client



####################################################################
#
####################################################################
def checkPayload(message):
    payload=message.payload
    try:
        payload=payload.decode("utf-8")
    except (Exception) as e:
        gv.logger.error('-'*30)
        gv.logger.error('topic:         %s', message.topic)
        gv.logger.error('payload error: %s', payload)
        gv.logger.error('    exception: %s', e)
        gv.logger.error('-'*30)
        return None

    try:
        payload=benedict(json.loads(payload))
    except (Exception) as e:
        pass # payload is a str

    return payload



####################################################################
#
####################################################################
def on_message(client, userdata, message):
    gv.publish_timer.restart() # if message has been received means application is alive.
    gv.logger.info("Received:")
    full_topic=message.topic

    if message.retain==1:
        gv.logger.notify("   topic: %s - retained: %s", full_topic, message.retain)
        gv.logger.notify("   payload: %s", message.payload)
        if full_topic=='tele/xxxxxVecoviNew/LWT': # forzatura per uno specifico....
            clear_retained_topic(client, message)
    else:
        gv.logger.info("   topic: %s", full_topic)
        gv.logger.info("   payload: %s", message.payload)

    payload=checkPayload(message)

    if gv.clear_retained and message.retain:
        clear_retained_topic(client, message)





    """viene rilasciato automaticamente da tasmota
        topic='tasmota/discovery/DC4F22D3B32F/sensors'
        topic='tasmota/discovery/DC4F22D3B32F/config'
    cambiare il topic attraverso il MAC """
    if full_topic.startswith("tasmota/discovery"):
        _tasmota, _discovery, _mac,  suffix, *rest=full_topic.split('/')
        if _mac and not ":" in _mac:
            _mac=':'.join(_mac[i:i+2] for i in range(0,12,2))

        if "t" in payload: # contains topic_name
            topic_name=payload["t"]
            if (device:=gv.devicesDB.getDeviceInstance(mac=_mac)) is None:
                gv.logger.error("MAC: %s [topic: %s] NOT found in devicesDB.", _mac, full_topic)
                return
        else:
            return

        full_topic=f'tasmota/{topic_name}/{suffix}'


    first_qualifier, topic_name, *rest=full_topic.split('/')

    if first_qualifier in ["LnCmnd"]:
        LnCmnd.process(topic=message.topic, payload=payload, mqttClient_CB=client)
        return


    # ------------------------------------------------------
    # - prendiamo le caratteristiche del device
    # - device è un object_class e non un dictionary
    # ------------------------------------------------------
    if (device:=gv.devicesDB.getDeviceInstance(dev_name=topic_name)) is None:
        gv.logger.error("tgGroup: '%s' [topic: %s]  NOT found in devicesDB - payload: %s", topic_name, full_topic, payload)
        return




    """ create relative class_type intance
        include also deviceDB data
    """
    if device.type=="tasmota":
        # se non presente nella lista dinamica tasmotaDevices
        if not device.name in gv.tasmotaDevices.keys():
            dynamic_dev=TasmotaClass(device_class=device, gVars=gv)
            gv.tasmotaDevices[device.name]=dynamic_dev
            # dynamic_dev.deviceDB=device ### aggiungiamo lo static_device al dynamic_device
        else:
            dynamic_dev=gv.tasmotaDevices[device.name]


        dynamic_dev.processMqttMessage(topic=full_topic, payload=payload, mqttClient_CB=client)


    elif device.type=='shelly':
        err_msg="per gli shelly non ancora implementato"
        gv.logger.warning(err_msg)

    elif device.type=='application':
        err_msg="per i gruppi tipo application non ancora implementato"
        gv.logger.warning(err_msg)

    else:
        err_msg=f"{full_topic} non ancora implementato"
        gv.logger.warning(err_msg)










    # if gv.just_monitor:
    #     pass

    # elif first_qualifier in ["shellies"]:
    #     Shellies_Device.process(topic=message.topic, payload=payload, mqttClient_CB=client)

    # elif first_qualifier in ["LnCmnd"]:
    #     LnCmnd.process(topic=message.topic, payload=payload, mqttClient_CB=client)

    # elif first_qualifier in ["cmnd", "tele", "stat", "tasmota", "LnTelegram"]:
    #     Tasmota_Device.process(topic=message.topic, payload=payload, mqttClient_CB=client)


    # else:
    #     gv.logger.error('%s: NOT managed. payload: %s', message.topic, payload)



####################################################################
#
####################################################################
def on_message_prev(client, userdata, message):
    gv.publish_timer.restart() # if message has been received means application is alive.


    gv.logger.info("Received:")
    if message.retain==1:
        gv.logger.notify("   topic: %s - retained: %s", message.topic, message.retain)
        gv.logger.notify("   payload: %s", message.payload)
        if message.topic=='tele/xxxxxVecoviNew/LWT': # forzatura per uno specifico....
            clear_retained_topic(client, message)
    else:
        gv.logger.info("   topic: %s", message.topic)
        gv.logger.info("   payload: %s", message.payload)

    payload=checkPayload(message)

    if gv.clear_retained and message.retain:
        clear_retained_topic(client, message)


    first_qualifier, *rest=message.topic.split('/')

    if gv.just_monitor:
        pass

    elif first_qualifier in ["shellies"]:
        Shellies_Device.process(topic=message.topic, payload=payload, mqttClient_CB=client)

    elif first_qualifier in ["LnCmnd"]:
        LnCmnd.process(topic=message.topic, payload=payload, mqttClient_CB=client)

    elif first_qualifier in ["cmnd", "tele", "stat", "tasmota", "LnTelegram"]:
        Tasmota_Device.process(topic=message.topic, payload=payload, mqttClient_CB=client)


    else:
        gv.logger.error('%s: NOT managed. payload: %s', message.topic, payload)



####################################################################
#
####################################################################
def subscribe(client: mqtt_client, topics: list):
    for topic in topics:
        gv.logger.info('Subscribing... %s', topic)
        client.subscribe(topic)
    client.on_message = on_message





####################################################################
#
####################################################################
def run(gVars: dict):
    global gv
    gv=gVars
    topic_list = gv["topics"]
    gv.tasmotaDevices={}
    gv.macTable={}



    ### - get application info from deviceDB
    if (appl_device := gv.devicesDB.getDeviceInstance(dev_name=gv.tg_group_name)):
        assert appl_device.type=="application"
        # appl_tg=appl_device.tg
    else:
        gv.logger.error("%s NOT found in devicesDB.", gv.tg_group_name)
        sys.exit(1)

    gv.appl_device=appl_device

    ### initialize my modules
    TSM.setup(gVars)
    Tasmota_Device.setup(gVars)
    Shellies_Device.setup(gVars)
    LnCmnd.setup(gVars)
    tgNotify.setup(gVars)





    ### check if a specific topics are entered
    topics=topic_list[:]
    for topic in topics:
        device=gv.devicesDB.getDeviceInstance(dev_name=topic)
        if device:
            topic_list.remove(topic)
            topic_name=device.name
            mac=device.mac.replace(":", "")
            topic_list.append(f'+/{topic_name}/#')
            if device.type=="tasmota":
                topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC

    else:
        if not '+/#' in topic_list:
            topic_list.append('tasmota/discovery/#')

    topic_list.append('LnCmnd/#')

    client_id = f'LnMqttMonitor-{random.randint(0, 1000)}'
    client=connect_mqtt(client_id)
    gv.client=client

    gv.publish_timer=LnTimer(name='mqtt publish', default_time=100, logger=gv.logger)
    gv.publish_timer.start()

    subscribe(client, topic_list)


    if gv.just_monitor:
        client.loop_forever()


    client.loop_start()
    TSM.send_html(tg_group=appl_device.tg, message="application has been started!", caller=True, notify=True)
    time.sleep(4) # Wait for connection setup to complete


    print('Started...')
    systemChannelName=f"{hostname}"

    while True:
        mm=int(time.strftime("%M"))
        hh=int(time.strftime("%H"))
        ss=int(time.strftime("%S"))

        if mm==0:
            if hh in gv.config['main.send_status_hours']:
                Tasmota_Device.sendStatus()

            if hh in gv.config['main.still_alive_interval_hours']:
                savePidFile(gv.args.pid_file)
                TSM.send_html(tg_group=appl_device.tg, message="I'm still alive!", caller=True, notify=False)


        gv.logger.info('publishing ping mqtt message to restart publish_timer')
        result=client.publish(topic='LnCmnd/mqtt_monitor_application/ping', payload='publish timer', qos=0, retain=False)

        """ ho notato che dopo un pò il client va in hang e non cattura più
            i messaggi. Il codice che segue serve a monitorare lo status
            dell'applicazione e farla ripartire se necessario.
            publish_timer if exausted means that the application is NOT responding """
        if gv.publish_timer.remaining_time() <= 0:
            gv.logger.error('publish_timer - exausted')
            gv.logger.error('restarting application')
            TSM.send_html(tg_group=appl_device.tg, message="publish_timer - exausted - application is restarting!", caller=True, notify=False)

            os.kill(int(os.getpid()), signal.SIGTERM)



        time.sleep(60)







####################################################################
#
####################################################################
if __name__ == '__main__':
    logger=setColoredLogger()
    run(topic_list=['+/#'], my_logger=gv.logger)