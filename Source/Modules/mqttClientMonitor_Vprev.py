#!/usr/bin/env python3
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
from pathlib import Path

from    LnTimer import TimerLN as LnTimer
# from    savePidFile import savePidFile

import  LnCmnd_Process as LnCmnd
import  Tasmota_Telegram_Notification as tgNotify
import  TelegramSendMessage as TSM
from    Tasmota_Class import TasmotaClass

from devicesDB_sqLite import devicesDB_Class



#######################################################
# Intercetta il Ctrl-C
#######################################################
def signal_handler_Mqtt(signalLevel, frame):
    gv.logger.warning("signalLevel: %s", signalLevel)

    # client.Stop(termination_code=0, msg="signal_handler_Mqtt function") # stop mqtt and return
    gv.client.loop_stop()
    pid=os.getpid()

        ### chiudo il processo perché ci pensa systemD a farlo ripartire
    if gv.args.systemd:
        err_msg=f"MQTT server - Terminating on SIGTERM signalLevel [{signalLevel}] under systemd control "
        gv.logger.error(err_msg)
        # threading.Thread(target=shutdown).start()
        gv.telegramMessage.send_html(tg_group=gv.appl_device.tg, message=err_msg, caller=True) ### markdown dà errore
        os.kill(int(os.getpid()), signal.SIGTERM)
        sys.exit(1)


        ### Ctrl-c
    elif int(signalLevel)==2:
        print('\n'*3)
        choice = input("       Ctrl-c was pressed. [q]quit [any-key] restart \n\n")
        if choice == 'q':
            os.kill(int(os.getpid()), signal.SIGTERM)
            os.system("clear")
            sys.exit(1)

        ### restart using the same command line
        gv.logger.warning("MQTT server - Restarting on SIGINT [ctrl-c] signalLevel [%s]", signalLevel)
        command=f'ps -p {pid} -o args'
        splitted_cmd=shlex.split(command)
        output=subprocess.check_output(splitted_cmd, universal_newlines=True)
        cmd_line=output.split('\n')[1]
        splitted_cmd=shlex.split(cmd_line)
        gv.logger.warning('restarting: %s', splitted_cmd)
        os.execv(sys.executable, splitted_cmd)

        ### errore
    else:
        err_msg=f"MQTT server - Terminating on SIGTERM signalLevel [{signalLevel}]"
        gv.logger.error(err_msg)
        gv.telegramMessage.send_html(tg_group=gv.appl_device.tg, message=err_msg, caller=True) ### markdown dà errore
        sys.exit(1)


import signal
signal.signal(signal.SIGINT, signal_handler_Mqtt)



####################################################################
#  This function clears the retained flag by publishing
#  a empty message (msg=””) with the retained flag set.
####################################################################
def clear_retained_topic(client, message):
    _msg=str(message.payload.decode("utf-8"))
    gv.logger.notify('Trying to clear retained on message: %s topic: %s', _msg, message.topic)
    _msg=''
    result=client.publish(message.topic, _msg, qos=0, retain=True)
    gv.logger.notify(result)


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
            gv.telegramMessage.send_html(tg_group=gv.appl_device.tg, message=f"Failed to connect to mqtt, return code:{rc}", caller=True) ### markdown dà errore
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
        # auth=dict(broker.auth)

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    if broker.password:
        client.username_pw_set(broker.username, broker.password)
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
    gv.publish_timer.restart(seconds=100, stacklevel=4) # if message has been received means application is alive.

    gv.logger.notify("Received:\n")
    full_topic=message.topic
    payload=checkPayload(message)
    formatted_payload=payload.to_yaml() if isinstance(payload, benedict) else payload
    formatted_payload=payload

    if message.retain==1:
        gv.logger.notify("   topic: %s - retained: %s", full_topic, message.retain)
        gv.logger.notify("   payload: %s", formatted_payload)
        if full_topic=='tele/xxxxxVecoviNew/LWT': # forzatura per uno specifico....
            clear_retained_topic(client, message)
    else:
        gv.logger.notify("   topic: %s", full_topic)
        if gv.args.just_monitor:
            gv.logger.notify("   payload: %s", formatted_payload)
        else:
            gv.logger.debug("   payload: %s", formatted_payload)



    if gv.clear_retained and message.retain:
        clear_retained_topic(client, message)

    # gv.logger.info("full topic: %s", full_topic)

    """viene rilasciato automaticamente da tasmota
        topic='tasmota/discovery/DC4F22D3B32F/sensors'
        topic='tasmota/discovery/DC4F22D3B32F/config'
    risaliamo al topic_name attraverso il MAC """
    if full_topic.startswith("tasmota/discovery"):
        gv.logger.info("tasmota/discovery - [topic: %s]", full_topic)
        _tasmota, _discovery, _mac,  suffix, *rest=full_topic.split('/')
        if _mac and not ":" in _mac:
            _mac=':'.join(_mac[i:i+2] for i in range(0,12,2))

        if "t" in payload: # contains topic_name
            topic_name=payload["t"]
            if (obj_device := gv.devicesDB.getDevice(mac=_mac)) == {}:
                gv.logger.error("MAC: %s [topic: %s] NOT found in devicesDB.", _mac, full_topic)
                return
        else:
            return

        full_topic=f'tasmota/{topic_name}/{suffix}'

    ### JUST MONITOR
    if gv.args.just_monitor:
        return


    first_qualifier, topic_name, *rest=full_topic.split('/')

    if first_qualifier in ["LnCmnd"]:
        gv.logger.info("LnCmd - [topic: %s]", full_topic)
        LnCmnd.process(topic=message.topic, payload=payload, mqttClient_CB=client)
        return


    # ------------------------------------------------------
    # - prendiamo le caratteristiche del device
    # - device è un object_class e non un dictionary
    # ------------------------------------------------------
    # if topic_name=="Orto_4ch":
    #     import pdb; pdb.set_trace();print(topic_name) # by Loreto
    if (obj_device := gv.devicesDB.getDevice(name=topic_name)) == {}:
        # import pdb; pdb.set_trace();trace=True # by Loreto
        gv.logger.warning("tgGroup: '%s' [topic: %s]  NOT found in devicesDB - payload: %s", topic_name, full_topic, payload)
        return




    """ create relative class_type instance
        include also deviceDB data """


    if not obj_device:
        err_msg=f"{full_topic} NON lo vedo come device"
        gv.logger.warning(err_msg)
        return

    elif obj_device.type=="tasmota":
        if not obj_device.name in gv.tasmotaDevices.keys():
            """se non presente nella lista dinamica tasmotaDevices"""
            tasmota_device: tasmotaClass = TasmotaClass(obj_device=obj_device, gVars=gv)
            gv.tasmotaDevices[obj_device.name]: tasmotaClass = tasmota_device

            # facciamo il setup ed il refresh solo per quelli monitorati
            setupTasmotaDevice(client=client, tasmota_device=tasmota_device)
            # gv.tasmotaDevices[obj_device.name]["telegramNotification_timer"] = LnTimer(name=f'{obj_device.name} - telegramNotification_timer',
            #                                                                         start=True,
            #                                                                         default_time=60,
            #                                                                         stacklevel=3,
            #                                                                         logger=gv.logger)
            # gv.tasmotaDevices[obj_device.name].telegramNotification_timer.start(seconds=60, stacklevel=3) # stop noification for 120 seconds after start

            # print(gv.tasmotaDevices[obj_device.name].to_yaml())
            # import pdb; pdb.set_trace();trace=True # by Loreto

        else:
            tasmota_device: tasmotaClass = gv.tasmotaDevices[obj_device.name]


        tasmota_device.processMqttMessage(full_topic=full_topic, payload=payload, mqttClient_CB=client)


    elif obj_device.type=='shelly':
        err_msg="per gli shelly non ancora implementato"
        gv.logger.warning(err_msg)

    elif obj_device.type=='application':
        err_msg="per i gruppi tipo application non ancora implementato"
        gv.logger.warning(err_msg)

    else:
        err_msg=f"{full_topic} non ancora implementato"
        gv.logger.warning(err_msg)











####################################################################
#
####################################################################
def subscribe(client: mqtt_client, topic_list: list):
    full_topics=[]

    if "+/#" in topic_list:
        full_topics.append('+/#')
    else:
        for topic_name in topic_list:
            full_topics.append(f'+/{topic_name}/#')

        full_topics.append('LnCmnd/#')
        full_topics.append('tasmota/discovery/#')


    for topic in full_topics:
        gv.logger.info('Subscribing... %s', topic)
        client.subscribe(topic)
    client.on_message = on_message




####################################################################
#
####################################################################
def setupTasmotaDevice(client, tasmota_device: TasmotaClass):
    topic_name=tasmota_device.device_name

    # facciamo il setup ed il refresh del device interessato
    setup_commands = tasmota_device.setup_commands()
    setup_commands.insert(0, f"devicename {tasmota_device.device_name}")
    setup_commands.insert(0, f"topic {topic_name}")
    index = 0
    for name in tasmota_device.friendlyNames():
        index += 1
        setup_commands.insert(0, f"FriendlyName{index} {name}")

    payload=';'.join(setup_commands)

    # try:
    #     payload=';'.join(setup_commands)
    # except:
    #     import pdb; pdb.set_trace();trace=True # by Loreto
    gv.logger.info("sending setup_commands to: %s data: %s", topic_name, setup_commands)
    result=client.publish(topic=f"cmnd/{topic_name}/backlog", payload=payload, qos=0, retain=False)

    fREFRESH=True
    if fREFRESH:
        refresh_commands: list[str] = tasmota_device.refresh_commands()
        payload=';'.join(refresh_commands)
        gv.logger.info("sending refresh_commands to: %s data: %s", topic_name, refresh_commands)
        result=client.publish(topic=f"cmnd/{topic_name}/backlog", payload=payload, qos=0, retain=False)






####################################################################
#
####################################################################
def run(gVars: dict, main_config: dict, sqlite_config: dict):
    global gv
    gv=gVars

    #================= open mqtt DB  ==================
    db_filepath = Path(sqlite_config.db_filepath)
    mqtt_db_filepath = f'{db_filepath.parent}/{db_filepath.stem}_mqtt{db_filepath.suffix}'
    gv.devicesDB=devicesDB_Class(db_filepath=mqtt_db_filepath, close_after_read=False, logger=gv.logger)


    topic_list = gv.args.topics
    # topics_name_list = gv["topics"]
    gv.tasmotaDevices={}
    gv.macTable={}



    ### - get application info from deviceDB
    if (appl_device := gv.devicesDB.getDevice(name=gv.args.telegram_group_name)):
        assert appl_device.type=="application"
    else:
        gv.logger.error("%s NOT found in devicesDB.", gv.args.telegram_group_name)
        sys.exit(1)

    gv.appl_device = appl_device

    ### initialize my modules
    TSM.setup(gVars)
    LnCmnd.setup(gVars)
    tgNotify.setup(gVars)



    client_id = f'LnMqttMonitor-{random.randint(0, 1000)}'
    gv.logger.notify("mqtt client_ID: %s", client_id)
    # gv.broker = gv.devicesDB.getBroker(name=main_config.mqtt_broker_name)
    gv.broker = gv.devicesDB.getBroker(name=gv.args.broker_name)
    client=connect_mqtt(client_id)
    gv.client=client
    subscribe(client, topic_list)

    gv.publish_timer=LnTimer(name='mqtt publish', default_time=100, stacklevel=3, logger=gv.logger)
    gv.publish_timer.start(seconds=100, stacklevel=3)




    if gv.args.just_monitor:
        client.loop_forever()
        os.kill(int(os.getpid()), signal.SIGTERM)
        sys.exit(1)

    client.loop_start()

    TSM.send_html(tg_group=gv.appl_device.tg, message="application has been started!", caller=True, notify=True)
    time.sleep(4) # Wait for connection setup to complete


    print('Started...')
    systemChannelName=f"{hostname}"
    topic_ping = "LnCmnd/mqtt_monitor_application/ping"
    sleepTime=10
    last_publish_remaining_time = 0

    while True:
        mm=int(time.strftime("%M"))
        hh=int(time.strftime("%H"))
        ss=int(time.strftime("%S"))

        now=time.strftime("%H:%M:%S")
        gv.logger.notify("now is: %s", now)

        if mm==0:
            gv.logger.notify("hour o'clock")
            if hh in main_config['send_status_hours']:
                for name in gv.tasmotaDevices:
                    device=gv.tasmotaDevices[name]
                    device.sendStatus(payload={"alias": "summary"})


            if hh in main_config['still_alive_interval_hours']:
                # savePidFile(gv.args.pid_file)
                import pdb; pdb.set_trace();trace=True # by Loreto
                TSM.send_html(tg_group=gv.appl_device.tg, message="I'm still alive!", caller=True, notify=False)


        gv.logger.notify("publishing ping mqtt message to restart publish_timer: %s", topic_ping)
        result=client.publish(topic=topic_ping, payload="publish timer", qos=0, retain=False)

        """ ho notato che dopo un pò il client va in hang e non cattura più
            i messaggi. Il codice che segue serve a monitorare lo status
            dell'applicazione e farla ripartire se necessario.
            publish_timer if exausted means that the application is NOT responding """
        publish_remaining_time = gv.publish_timer.remaining_time()

        gv.logger.notify("publish remaining time: %s - last_publish_remaining_time: %s", publish_remaining_time, last_publish_remaining_time)

        if (gv.publish_timer.remaining_time() <= 0) or (publish_remaining_time == last_publish_remaining_time):
            gv.logger.error('publish_timer - exausted')
            gv.logger.error('restarting application')
            TSM.send_html(tg_group=gv.appl_device.tg, message="publish_timer - exausted - application is restarting!", caller=True, notify=False)

            os.kill(int(os.getpid()), signal.SIGTERM)
            sys.exit(1)

        last_publish_remaining_time = publish_remaining_time

        now=time.strftime("%H:%M:%S")
        gv.logger.notify("[%s] - vado in sleep: %s seconds", now, sleepTime)
        time.sleep(sleepTime)
        now=time.strftime("%H:%M:%S")
        gv.logger.notify("[%s] - esco dallo sleep di %s seconds", now, sleepTime)



####################################################################
#
####################################################################
if __name__ == '__main__':
    logger=setColoredLogger()
    run(topic_list=['+/#'], my_logger=gv.logger)