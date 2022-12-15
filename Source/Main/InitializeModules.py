# import  sys; sys.dont_write_bytecode = True
# import os

from types import SimpleNamespace

# def setup_envarsYamlLoader(*, gVars):
#     gv=SimpleNamespace()
#     gv.logger                  = gVars.logger
#     gv.prj_name                = gVars.prj_name
#     gv.envars_dir              = gVars.envars_dir
#     gv.mqttmonitor_runtime_dir = gVars.mqttmonitor_runtime_dir

#     from envarsYamlLoader import setup; setup(gVars=gv)


def setup_Telegram_Notification(*, gVars):
    gv=SimpleNamespace()
    gv.logger      = gVars.logger
    gv.prj_name    = gVars.prj_name

    from Telegram_Notification import setup; setup(gVars=gv)



def setup_LoadYamlFile_Class(*, gVars):
    import LoadYamlFile_Class; LoadYamlFile_Class.setup(gVars=gVars)



def setup_Topic_Process(*, gVars):
    import Topic_Process; Topic_Process.setup(gVars=gVars)



def setup_LnUtils(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    import LnUtils; LnUtils.setup(gVars=gv)



def Main(*, gVars):
    setup_Telegram_Notification(gVars=gVars)
    setup_LnUtils(gVars=gVars)
    setup_LoadYamlFile_Class(gVars=gVars)
    setup_Topic_Process(gVars=gVars)

