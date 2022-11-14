#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os

import  yaml, json
from    paho.mqtt import client as mqtt_client
import  uuid

import Topic_noThreads as Topic
THREADS=False
THREADS=True
# try:
# except:
#     import time
#     print('NOT USING THREADS')
#     time.sleep(5)
#     THREADS=False # per lanciare questo singolo file

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
        logger.error('payload error: %s', message.payload)
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


    # if payload: NON ricordo perché l'ho inserito
    logger.info("Received:")

    if message.retain==1:
        logger.warning("   topic: %s - retained: %s", message.topic, message.retain)
        logger.warning("   payload: %s", payload)
        if message.topic=='tele/xxxxxVecoviNew/LWT': # forzatura per uno specifico....
            clear_retained_topic(client, message)
    else:
        logger.info("   topic: %s", message.topic)
        logger.info("   payload: %s", payload)


    if CLEAR_RETAINED and message.retain:
        clear_retained_topic(client, message)

    if THREADS:
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
    global CLEAR_RETAINED, logger
    client = connect_mqtt()
    CLEAR_RETAINED=clear_retained
    logger=my_logger

    if THREADS:
        Topic.setup(my_logger=logger)

    if not '+/#' in topic_list:
        topic_list.append('tasmota/discovery/#')
        # topic_list.append('+/#')
    subscribe(client, topic_list)

    client.loop_forever()



####################################################################
#
####################################################################
if __name__ == '__main__':
    logger=setColoredLogger()
    run(topic_list=['+/#'], my_logger=logger)