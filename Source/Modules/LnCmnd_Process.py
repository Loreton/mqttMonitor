#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 15-03-2023 17.36.30

# https://github.com/python-telegram-bot/python-telegram-bot


import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)
from types import SimpleNamespace









def setup(gVars: SimpleNamespace):
    global gv
    gv=gVars





#########################################################
# TEST:
#    cmnd/TavoloLavoro/bcacklog power
#    cmnd/TavoloLavoro/bcacklog timers
#########################################################

#########################################################
#  Per comodità cerco di utilizzare il topic_name==Device_name
#########################################################
def process(topic, payload, mqttClient_CB):
    prefix, topic_name, suffix, *rest=topic.split('/')

    ### --------------
    if prefix=='LnCmnd':
        if topic=='LnCmnd/mqtt_monitor_application/query':
            gv.logger.notify('%s keepalive message has been received', topic)
            return

        ### -----------------------------------------------
        ### comandi derivanti da altre applicazioni per ottenere info
        ### da inviare a telegram group
        ### -----------------------------------------------
    elif first_qualifier in ["LnTelegram"]:
        tgNotify.telegram_notify(deviceObj=deviceObj, topic_name=topic_name, action=suffix, payload=payload)
        return



    else:
        gv.logger.warning("topic: %s not managed - payload: %s", topic, payload)

