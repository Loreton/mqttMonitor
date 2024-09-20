#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 17-05-2024 15.02.52

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)
from types import SimpleNamespace







#####################################
# gVars is benedict dictionary
#####################################
def setup(gVars: dict):
    global gv, C
    gv=gVars
    C=gv.logger.getColors()




#########################################################
# TEST:
#    cmnd/TavoloLavoro/bcacklog power
#    cmnd/TavoloLavoro/bcacklog timers
#########################################################

#########################################################
#  Per comodità cerco di utilizzare il topic_name==Device_name
#########################################################
def process(topic, payload, mqttClient_CB):
    gv.logger.caller('Entering in function...')

    prefix, topic_name, suffix, *rest=topic.split('/')

    ### --------------
    if prefix=='LnCmnd':
        if topic=='LnCmnd/mqtt_monitor_application/ping': # serve solo per far ripartire il publish_timer nel on_message()
            gv.logger.notify('%s keepalive message has been received', topic)
            return

        ### -----------------------------------------------
        ### comandi derivanti da altre applicazioni per ottenere info
        ### da inviare a telegram group
        ### -----------------------------------------------
    elif prefix in ["LnTelegram"]:
        tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, payload=payload)
        return



    else:
        gv.logger.warning("topic: %s not managed - payload: %s", topic, payload)

