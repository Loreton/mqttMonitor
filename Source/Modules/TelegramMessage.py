#!/usr/bin/python
#
# updated by ...: Loreto Notarantonio
# Date .........: 18-11-2022 16.37.18
#

import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)

import requests
import yaml, json
from LnDict import LoretoDict


###############################################
# keypath is string whith keys separated by dot
#       key1.key2.....keyn
# cast is the returned dictionary type (lortodict, OrderedDict, ...)
###############################################
def loadYamlFile(filename, cast: dict=dict, keypath: str=None):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content=f.read() # single string
    else:
        logger.error('File: %s not found', filename)
        sys.exit(1)

    my_data=yaml.load(content, Loader=yaml.SafeLoader)

    if keypath:
        ptr=my_data
        keypath=keypath.split('.')
        for key in keypath:
            ptr=ptr[key]

        my_data=ptr

    if 'loretodict' in str(cast).lower():  #  by Loreto:  18-11-2022 12.02.54
        return cast(my_data)
    else:
        return my_data



###############################################
#
###############################################
def get_bot_name(d, group_name):
    token=chat_id=bot_name=None
    for _bot_name in d.keys():
        bot=d[_bot_name]

        for group_type in ['groups', 'channels']:
            groups=bot.get(group_type)
            if not groups: continue
            for group in groups:
                if group.lower() == group_name.lower():
                    group_name=group # mettiamolo nel case corretto
                    chat_id=groups[group]['chat']['id']
                    token=bot['token']
                    bot_name=_bot_name
                    break

    return bot_name, token, chat_id, group_name



def telegramSend(group_name: str, message: dict, my_logger):
    global logger
    logger=my_logger
    yaml_file=os.path.expandvars("${ln_ENVARS_DIR}/yaml/telegramGroups.yaml")
    my_dict=loadYamlFile(yaml_file)
    my_bots=LoretoDict(my_dict['telegrambot'])

    bot_name, token, chat_id, groupName=get_bot_name(d=my_bots, group_name=group_name)

    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"

    logger.warning('url:  %s',   url)
    if bot_name and token and chat_id:
        try:
            response = requests.get(url).json()
            logger.info('   response: %s',   response)
        except (Exception) as ex:
            logger.error('     exception:   %s',   str(ex))

    else:
        logger.error('command cannot be executed....missing some value!')
        logger.error('     bot_name:   %s',   bot_name)
        logger.error('     token:      %s',   token)
        logger.error('     group_name: %s',   groupName)
        logger.error('     chat_id:    %s',   chat_id)

