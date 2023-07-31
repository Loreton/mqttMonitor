#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 30-07-2023 11.58.54



import  sys; sys.dont_write_bytecode = True
import  os
from types import SimpleNamespace






def setup(**kwargs):
    global gv
    gv=SimpleNamespace()

    gv.logger=kwargs["logger"]
    gv.devicesDB=kwargs["devicesDB"]



def process(topic, payload, mqttClient_CB):
    prefix, topic_name, suffix, *rest=topic.split('/')

    ### --------------
    if prefix=='LnCmnd':
        if topic=='LnCmnd/mqtt_monitor_application/query':
            gv.logger.notify('%s keepalive message has been received', message.topic)
            return

    else:
        gv.logger.warning("topic: %s not managed - payload: %s", topic, payload)

