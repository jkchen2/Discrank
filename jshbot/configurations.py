import discord
import logging
import json
import os.path

from jshbot.exceptions import BotException, ErrorTypes

def get_configurations(bot):
    configurations_list = {}
    directory = bot.path + "/config"
    try:
        with open(bot_directory + '/config.json', 'r') as config_file:
            configurations_list['core'] = json.load(config_file)
    except:
        raise BotException(ErrorTypes.FATAL, EXCEPTION,
                "Could not open the core configuration file")

    return configurations_list
