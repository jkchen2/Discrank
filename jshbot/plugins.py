import asyncio
import discord
import logging
import os.path
import importlib.util

from jshbot import core, configurations, commands
from jshbot.exceptions import ErrorTypes, BotException

EXCEPTION = 'Plugins'

def get_plugins(bot):
    '''
    Gets a list of all of the plugins and stores them as a key/value pair of
    the plugin name and the module itself (renamed to plugin for the user).
    '''
    directory = bot.path + '/plugins'
    try:
        plugins_list = os.listdir(directory)
    except:
        raise BotException(ErrorTypes.STARTUP, EXCEPTION,
                "Plugins directory not found")
    valid_plugins = {}

    # Add base plugin
    from jshbot import base
    command_pairs, shortcuts, manual = base.get_commands()
    commands.add_commands(bot, command_pairs, 'base')
    commands.add_commands(bot, shortcuts, 'base')
    commands.add_manual(bot, manual)
    valid_plugins['base'] = base

    for plugin in plugins_list:
        if plugin[0] in ('.', '_') or plugin == 'base': # Dang swap files
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                    plugin, directory + '/{}'.format(plugin))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            command_pairs, shortcuts, manual = module.get_commands()
            commands.add_commands(bot, command_pairs, plugin)
            commands.add_commands(bot, shortcuts, plugin)
            commands.add_manual(bot, manual)
        except Exception as e:
            raise BotException(ErrorTypes.STARTUP, EXCEPTION,
                    "Failed to import external plugin", plugin, e=e)
        else:
            logging.debug("Adding plugin {}".format(plugin))
            valid_plugins[plugin] = module

    if len(valid_plugins):
        logging.debug("Loaded {} plugin(s)".format(len(valid_plugins)))
    
    return valid_plugins

def on_message_broadcast(bot, message):
    logging.debug("on_message_broadcast")
    pass

def on_ready_broadcast(bot):
    logging.debug("on_ready_broadcast")
    pass

