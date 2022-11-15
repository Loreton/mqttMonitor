#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os, signal

import  yaml, json
from    paho.mqtt import client as mqtt_client
import  uuid
import  time
import  subprocess, shlex

import Topic_noThreads as Topic
from TelegramMessage import telegramSend
from LnTimer import TimerLN as LnTimer

##########################################################################
# https://coloredlogs.readthedocs.io/en/latest/readme.html#installation
# https://coloredlogs.readthedocs.io/en/latest/api.html#changing-the-colors-styles
##########################################################################
def setColoredLogger(logging_file=None):
    import logging
    from logging.handlers import RotatingFileHandler
    import colorlog

    def add_StreamingHandler():
        from colorlog import ColoredFormatter
        c_formatter = ColoredFormatter(
            "%(green)s%(asctime)s %(log_color)s%(levelname)-4s %(purple)s[%(funcName)s:%(lineno)4s]: %(log_color)s%(message)s",
            datefmt="%H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )

        c_handler=logging.StreamHandler()
        c_handler.setFormatter(c_formatter)
        logger.addHandler(c_handler)



    # logger=logging.getLogger(__name__)
    logger=colorlog.getLogger(__name__)
    logger.setLevel('DEBUG') # ROOT level - decide il livello massimo
    add_StreamingHandler()


    logger.debug("this is a debugging message")
    logger.info("this is an informational message")
    logger.warning("this is a warning message")
    logger.error("this is an error message")
    logger.critical("this is a critical message")

    return logger


'''
https://community.openhab.org/t/clearing-mqtt-retained-messages/58221
     sudo systemctl stop mosquitto.service
     sudo rm /var/lib/mosquitto/mosquitto.db
       Delete the mosquitto.db containing all the stored message data in the persistence.
           By default, located in /var/lib/mosquitto/mosquitto.db
     sudo systemctl start mosquitto.service


    mosquitto_pub -h hostname -t the/topic -u username -P password -n -r -d
        -n = Send a null (zero length) message
        -r = Retain the message as a “last known good” value on the broker
        -d = Enable debug messages

'''


####################################################################
#  This function clears the retained flag by publishing
#  a empty message (msg=””) with the retained flag set.
####################################################################
def clear_retained_topic(client, message):
    _msg=str(message.payload.decode("utf-8"))
    logger.warning('Trying to clear retained on message: %s topic: %s', _msg, message.topic)
    _msg=''
    result=client.publish(message.topic, _msg, qos=0, retain=True)
    logger.warning(result)


####################################################################
#
####################################################################
def connect_mqtt() -> mqtt_client:
    client_id='lnmqtt' + str(uuid.uuid4())
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
        else:
            logger.info("Failed to connect, return code %d\n", rc)

    def on_disconnect(client, userdata, rc):
        logging.info("disconnecting reason  "  +str(rc))
        client.connected_flag=False
        client.disconnect_flag=True


    filename=os.path.expandvars("${ln_ENVARS_DIR}/yaml/Mqtt_Brokers.yaml")
    with open(filename, 'r') as f:
        content=f.read() # single string
    my_brokers=yaml.load(content, Loader=yaml.SafeLoader)

    HIVE_MQ=False
    if HIVE_MQ:
        print('da implemetare')
        sys.exit(1)
    else:
        broker=my_brokers['brokers']['lnpi22']
        url=broker['url']
        port=broker['port']
        auth=broker['auth']

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    if auth: client.username_pw_set(**auth)
    client.connect(url, int(port))
    return client


####################################################################
#
####################################################################
def checkPayload(payload):
    try:
        payload=payload.decode("utf-8")
    except (Exception) as e:
        logger.error('payload error: %s', payload)
        logger.error('    exception: %s', e)
        return None

    try:
        payload=json.loads(payload)
    except (Exception) as e:
        pass # payload is a str


    return payload

####################################################################
#
####################################################################
def on_message(client, userdata, message):
    payload=checkPayload(message.payload)

    if message.topic=='LnCmnd/mqtt_monitor_application/query':
        logger.notify('%s keepalive message has been received', message.topic)
        publish_timer.restart() # if message has been received means application is alive.
        return


    # if payload: NON ricordo perché l'ho inserito
    logger.info("Received:")

    if message.retain==1:
        logger.warning("   topic: %s - retained: %s", message.topic, message.retain)
        logger.warning("   payload: %s", payload)
        if message.topic=='tele/xxxxxVecoviNew/LWT': # forzatura per uno specifico....
            clear_retained_topic(client, message)
    else:
        logger.info("   topic: %s", message.topic)
        logger.debug("   payload: %s", payload)


    if CLEAR_RETAINED and message.retain:
        clear_retained_topic(client, message)

    Topic.process(topic=message.topic, payload=payload, mqttClient_CB=client)




####################################################################
#
####################################################################
def subscribe(client: mqtt_client, topics: list):
    for topic in topics:
        logger.info('Subscribing... %s', topic)
        client.subscribe(topic)
    client.on_message = on_message





####################################################################
#
####################################################################
def run(my_logger, topic_list: list=['+/#'], clear_retained: bool=False):
    global CLEAR_RETAINED, logger,  myself_timer, publish_timer, client
    client = connect_mqtt()
    CLEAR_RETAINED=clear_retained
    logger=my_logger

    publish_timer=LnTimer(name='ping publish', default_time=100, start=False, logger=logger)
    publish_timer.start()

    # myself_timer=LnTimer(name='ping mySelf', default_time=6, start=False, logger=logger)
    # myself_timer.start()


    Topic.setup(my_logger=logger)
    topic_list.append('LnCmnd/#')

    if not '+/#' in topic_list:
        topic_list.append('tasmota/discovery/#')
        # topic_list.append('+/#')
    subscribe(client, topic_list)

    '''
    fFOREVER=False
    if fFOREVER:
        client.loop_forever()
    '''


    """ ho notato che dopo un pò il client va in hang e non cattura più
        i messaggi. Il codice che segue serve a monitorare lo status
        dell'applicazione e farla ripartire se necessario.
    """
    client.loop_start()
    telegramSend(group_name='Ln_MqttMonitor', message="application has been started!", logger=logger)
    time.sleep(4) # Wait for connection setup to complete


    print('Started...')

    while True:
        """ publish_timer if exausted means that the application is responding """
        if publish_timer.is_exausted(logger=logger.debug):
            logger.error('publish_timer - exausted')
            logger.error('restarting application')
            telegramSend(group_name='Ln_MqttMonitor', message="publish_timer - exausted - application is restarting!", logger=logger)
            os.kill(int(os.getpid()), signal.SIGINT)


        time.sleep(60)
        logger.info('send publih check message')
        result=client.publish(topic='LnCmnd/mqtt_monitor_application/query', payload='publish timer', qos=0, retain=False)





#######################################################
# Intercetta il Ctrl-C
#######################################################
def signal_handler_Mqtt(signalLevel, frame):
    logger.warning("signalLevel: %s", signalLevel)

    # client.Stop(termination_code=0, msg="signal_handler_Mqtt function") # stop mqtt and return
    client.loop_stop()
    pid=os.getpid()

    # if systemd:
    #     logger.warning("MQTT server - Terminating on SIGTERM signalLevel [%s] under systemd control ", signalLevel)
    #     # threading.Thread(target=shutdown).start()
    #     sys.exit(1)

    if int(signalLevel)==2:
        print('\n'*5)
        logger.warning("MQTT server - Restarting on SIGINT [ctrl-c] signalLevel [%s]", signalLevel)
        command=f'ps -p {pid} -o args'
        splitted_cmd=shlex.split(command)
        output=subprocess.check_output(splitted_cmd, universal_newlines=True)
        cmd_line=output.split('\n')[1]
        splitted_cmd=shlex.split(cmd_line)
        logger.warning('restarting: %s', splitted_cmd)
        print('\n'*5)
        # time.sleep(2)
        # input('Press enter to continue...')
        os.execv(sys.executable, splitted_cmd)
    else:
        logger.warning("MQTT server - Terminating on SIGTERM signalLevel [%s]", signalLevel)
        sys.exit(1)


import signal
signal.signal(signal.SIGINT, signal_handler_Mqtt)



####################################################################
#
####################################################################
if __name__ == '__main__':
    logger=setColoredLogger()
    run(topic_list=['+/#'], my_logger=logger)