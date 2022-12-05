# import  sys; sys.dont_write_bytecode = True
# import os

from types import SimpleNamespace

def setup_envarsYamlLoader(*, gVars):
    gv=SimpleNamespace()
    gv.logger                  = gVars.logger
    gv.envars_dir              = gVars.envars_dir
    gv.mqttmonitor_runtime_dir = gVars.mqttmonitor_runtime_dir

    from envarsYamlLoader import setup; setup(gVars=gv)


def setup_MqttTxRx(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    from MqttTxRx import setup; setup(gVars=gv)



def setup_LoretoDict(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    from LoretoDict import setup; setup(gVars=gv)


def setup_sendTasmotaCommands(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    gv.broker_name=gVars.broker_name

    from sendTasmotaCommands import setup; setup(gVars=gv)


def Main(*, gVars):
    setup_LoretoDict(gVars=gVars)
    # setup_MqttTxRx(gVars=gVars)
    setup_envarsYamlLoader(gVars=gVars)
    # setup_sendTasmotaCommands(gVars=gVars)