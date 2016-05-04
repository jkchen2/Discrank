import discord
import logging
import json
import os.path

from jshbot.exceptions import BotException, ErrorTypes

EXCEPTION = 'Configurations'

def get_configurations(bot):
    configurations_list = {}
    directory = bot.path + '/config'
    try:
        with open(directory + '/config.json', 'r') as config_file:
            configurations_list['core'] = json.load(config_file)
    except Exception as e:
        raise BotException(ErrorTypes.FATAL, EXCEPTION,
                "Could not open the core configuration file", e=e)

    return configurations_list
