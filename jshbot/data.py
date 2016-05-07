import discord
import asyncio
import logging
import os
import threading

from jshbot.exceptions import ErrorTypes, BotException

EXCEPTION = 'Data'
write_lock = threading.Lock()

def get_directories(bot):
    '''
    Gets the data directories of all of the plugins. This will create them if
    they don't exist already.
    '''
    directories = {}
    for plugin_name in bot.plugins:
        directory = bot.path + '/data/' + plugin_name
        if not os.path.exists(directory):
            os.makedirs(directory)
        directories[plugin_name] = os.listdir()

    return directories

