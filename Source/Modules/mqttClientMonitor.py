#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
from types import SimpleNamespace

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
def connect_mqtt() -> mqtt_client:
    client_id='lnmqtt' + str(uuid.uuid4())
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            gv.logger.info("Connected to MQTT Broker!")
        else:
            gv.logger.info("Failed to connect, return code %d\n", rc)
            gv.telegramMessage.send_html(group_name=gv.tgGroupName, message=f"Failed to connect to mqtt, return code:{rc}", caller=True) ### markdown dà errore
            os.kill(int(os.getpid()), signal.SIGTERM)
            sys.exit(1)


    def on_disconnect(client, userdata, rc):
        logging.info("disconnecting reason: %s", rc)
        client.loop_stop()
        client.connected_flag=False
        client.disconnect_flag=True


    # filename=os.path.expandvars("${ln_ENVARS_DIR}/yaml/Mqtt_Brokers.yaml")
    # with open(filename, 'r') as f:
    #     content=f.read() # single string
    # my_brokers=yaml.load(content, Loader=yaml.SafeLoader)


    HIVE_MQ=False
    if HIVE_MQ:
        print('da implemetare')
        sys.exit(1)
    else:
        # broker=mqttBroker(broker_name="LnMqtt")
        broker=gv.broker
        url=broker['url']
        port=broker['port']
        auth=broker['auth']

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    if auth: client.username_pw_set(**auth)
    rcode=client.connect(url, int(port))
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
        # Topic.process(topic=message.topic, payload=payload, mqttClient_CB=client)
        Tasmota_Device.process(topic=message.topic, payload=payload, mqttClient_CB=client)


    else:
        gv.logger.error('%s: NOT managed. payload: %s', message.topic, payload)
        import pdb; pdb.set_trace(); pass # by Loreto



####################################################################
#
####################################################################
def on_message_OK(client, userdata, message):
    import  Topic_Process as Topic

    gv.publish_timer.restart() # if message has been received means application is alive.

    # payload=checkPayload(message.payload)
    payload=checkPayload(message)

    if message.topic=='LnCmnd/mqtt_monitor_application/query':
        gv.logger.notify('%s keepalive message has been received', message.topic)
        return


    # if payload: NON ricordo perché l'ho inserito
    gv.logger.info("Received:")

    if message.retain==1:
        gv.logger.notify("   topic: %s - retained: %s", message.topic, message.retain)
        gv.logger.notify("   payload: %s", payload)
        if message.topic=='tele/xxxxxVecoviNew/LWT': # forzatura per uno specifico....
            clear_retained_topic(client, message)
    else:
        gv.logger.info("   topic: %s", message.topic)
        gv.logger.debug("   payload: %s", payload)


    if gv.clear_retained and message.retain:
        clear_retained_topic(client, message)

    if not gv.just_monitor:
        Topic.process(topic=message.topic, payload=payload, mqttClient_CB=client)




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
def run(gVars: SimpleNamespace):
    global gv
    gv     = gVars
    gv.devices=dict()
    gv.macTable=dict()
    gv.tgGroupName  = gv.args.telegram_group_name
    gv.just_monitor = gv.args.just_monitor
    gv.topic_list   = gv.args.topics

    ### initialize my modules
    Tasmota_Device.setup(gVars=gv)
    Shellies_Device.setup(gVars=gv)
    LnCmnd.setup(gVars=gv)
    tgNotify.setup(gVars=gv)


    client=connect_mqtt()
    gv.client=client

    gv.publish_timer=LnTimer(name='mqtt publish', default_time=100, logger=gv.logger)
    gv.publish_timer.start()

    dev_name=gv.topic_list[0].lower()
    # Topic.setup(gVars=gv)
    ### per debug inseriamo un singolo device
    if dev_name =='tavololavoro':
        topic_name='TavoloLavoro'
        mac='C82B964FD367'
        gv.topic_list.append(f'+/{topic_name}/#')
        # gv.topic_list.append(f'LnCmnd/#')
        # gv.topic_list.append(f'LnCmnd/{topic_name}/#')
        # gv.topic_list.append(f'LnCmnd/mqtt_monitor_application/#')
        gv.topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC di TavoloLavoro

    elif dev_name =='vescovinew':
        topic_name='VescoviNew'
        mac='C44F33978EFA'
        gv.topic_list.append(f'+/{topic_name}/#')
        gv.topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC di TavoloLavoro

    elif dev_name =='computercasetta':
        topic_name='ComputerCasetta'
        mac='BC:DD:C2:85:AB:47'.replace(':', '')
        gv.topic_list.append(f'+/{topic_name}/#')
        gv.topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC di TavoloLavoro

    elif dev_name =='beverino_01':
        topic_name='Beverino_01'
        mac='DC4F2292DFAF'
        gv.topic_list.append(f'+/{topic_name}/#')
        gv.topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC di TavoloLavoro

    elif dev_name =='scaldasonno':
        topic_name='Scaldasonno'
        mac='8CAAB5614B69'
        gv.topic_list.append(f'+/{topic_name}/#')

    elif dev_name =='farolegnaia':
        topic_name='FaroLegnaia'
        mac='BCDDC285AEEB'
        gv.topic_list.append(f'+/{topic_name}/#')
        gv.topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC di TavoloLavoro

    elif dev_name =='presscontrol':
        topic_name='PressControl'
        mac='600194C24001'
        gv.topic_list.append(f'+/{topic_name}/#')
        gv.topic_list.append(f'tasmota/discovery/{mac}/#') ### MAC di TavoloLavoro

    else:
        if not '+/#' in gv.topic_list:
            gv.topic_list.append('tasmota/discovery/#')


    gv.topic_list.append('LnCmnd/#')
    subscribe(client, gv.topic_list)


    if gv.just_monitor:
        client.loop_forever()


    client.loop_start()
    # STM.sendMsg(group_name=gv.tgGroupName, message="application has been started!", my_logger=gv.logger, caller=True, parse_mode='MarkDown')
    # STM.sendMsg(group_name=gv.tgGroupName, message="application has been started!", my_logger=gv.logger, caller=True, parse_mode='html') ### markdown dà errore
    gv.telegramMessage.send_html(group_name=gv.tgGroupName, message="application has been started!", caller=True) ### markdown dà errore
    time.sleep(4) # Wait for connection setup to complete


    print('Started...')
    systemChannelName=f"{hostname}"

    while True:
        mm=time.strftime("%M")
        hh=time.strftime("%H")
        ss=time.strftime("%S")

        # if int(mm)==0 and int(hh)>6 and int(hh)<22:
        # if int(mm)==0 and int(hh)%12: # ogni 12 ore...
        if int(mm)==0 and int(hh) in [6, 12, 18, 22]: # ogni 12 ore...
            Topic.sendStatus()



        # if int(mm) in [0, 15, 30, 45]:
        if int(hh) in gv.config['main.still_alive_interval_hours'] and int(mm) in [0]:
            savePidFile(gv.args.pid_file)
            gv.telegramMessage.send_html(group_name=gv.tgGroupName, message="I'm still alive!", caller=True)


        gv.logger.info('publishing check/ping mqtt message')
        result=client.publish(topic='LnCmnd/mqtt_monitor_application/query', payload='publish timer', qos=0, retain=False)

        """ ho notato che dopo un pò il client va in hang e non cattura più
            i messaggi. Il codice che segue serve a monitorare lo status
            dell'applicazione e farla ripartire se necessario.
            publish_timer if exausted means that the application is NOT responding """
        if gv.publish_timer.remaining_time() <= 0:
            gv.logger.error('publish_timer - exausted')
            gv.logger.error('restarting application')
            gv.telegramMessage.send(group_name=gv.tgGroupName, message="publish_timer - exausted - application is restarting!", caller=True)

            os.kill(int(os.getpid()), signal.SIGTERM)



        time.sleep(60)







####################################################################
#
####################################################################
if __name__ == '__main__':
    logger=setColoredLogger()
    run(topic_list=['+/#'], my_logger=gv.logger)