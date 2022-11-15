#!/usr/bin/python
#
# updated by ...: Loreto Notarantonio
# Date .........: 15-11-2022 08.50.31
#

import sys; sys.dont_write_bytecode = True
import os
import requests
import yaml, json
from LnDict import LoretoDict


###############################################
#
###############################################
def loadYamlFile(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content=f.read() # single string
    else:
        self.logger.error('File: %s not found', filename)
        sys.exit(1)

    my_dict=yaml.load(content, Loader=yaml.SafeLoader)

    return my_dict

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



def telegramSend(group_name: str, message: dict, logger):
    yaml_file="${ln_ENVARS_DIR}/yaml/telegrambot.yaml"
    yaml_file=os.path.expandvars(yaml_file)
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

