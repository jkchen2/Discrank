import asyncio
import discord
import logging
import os.path
import importlib.util
import sys

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
    valid_plugins['base'] = [base]

    # Get plugin commands
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
            valid_plugins[plugin] = [module]

    # Get functions to broadcast
    events = ['on_ready', 'on_error', 'on_message', 'on_socket_raw_receive',
            'on_socket_raw_send', 'on_message_delete', 'on_message_edit', 
            'on_channel_delete', 'on_channel_create', 'on_channel_update', 
            'on_member_join', 'on_member_update', 'on_server_join',
            'on_server_remove', 'on_server_update', 'on_server_role_create',
            'on_server_role_delete', 'on_server_role_update',
            'on_server_available', 'on_server_unavailable',
            'on_voice_state_update', 'on_member_ban', 'on_member_unban',
            'on_typing']
    for plugin_name, plugin in valid_plugins.items():
        functions = []
        for event in events:
            functions.append(getattr(plugin[0], event, None))
        valid_plugins[plugin_name].append(functions)

    if len(valid_plugins):
        logging.debug("Loaded {} plugin(s)".format(len(valid_plugins)))

    return valid_plugins

def broadcast_event(bot, event_index, *args):
    '''
    Loops through all of the plugins and looks to see if the event index
    specified is associated it. If it is, call that function with args.
    '''
    for plugin_name, plugin_pair in bot.plugins.items():
        function = plugin_pair[1][event_index]
        if function:
            asyncio.ensure_future(function(bot, *args))

