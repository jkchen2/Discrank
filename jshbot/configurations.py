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
        raise BotException(ErrorTypes.STARTUP, EXCEPTION,
                "Could not open the core configuration file", e=e)

    directory += '/'
    for plugin in bot.plugins:
        try:
            with open(directory + plugin + '.json', 'r') as config_file:
                configurations_list[plugin] = json.load(config_file)
        except FileNotFoundError:
            if bot.plugins[plugin][0].uses_configuration:
                raise BotException(ErrorTypes.STARTUP, EXCEPTION,
                        "Plugin " + plugin + " requires a configuration file, "
                        "but it was not found.")
        except Exception as e:
            raise BotException(ErrorTypes.STARTUP, EXCEPTION,
                    "Could not open the " + plugin + " configuration file.",
                    e=e)

    return configurations_list
