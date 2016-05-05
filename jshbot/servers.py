import asyncio
import discord
import logging
import os.path
import threading
import json

import sys

from jshbot.exceptions import ErrorTypes, BotException

EXCEPTION = 'Servers'
write_lock = threading.Lock()

def get_servers_data(bot):
    directory = bot.path + "/data"
    try:
        with open(directory + '/servers.json', 'r') as servers_file:
            return json.load(servers_file)
    except Exception as e:
        logging.error("Could not open the servers data file")
        print(e)
        return {}

def add_server(bot, server):
    # NOTE: Can't use sets because they aren't JSON serializable :c
    bot.servers_data[server.id] = {
            'muted':False,
            'muted_channels':[],
            'moderators':[],
            'blocked':[]
            }

def update_server_information(bot, server, **kwargs):
    try:
        bot.servers_data[server.id].update(kwargs)
    except KeyError: # Server doesn't exist. Create it.
        logging.debug("Automatically creating server {}".format(server))
        add_server(bot, server)
        update_server_information(bot, server, kwargs)

def check_all(bot):
    '''
    Checks that the bot has not missed any additions or removals in servers
    and channels.
    '''
    for server in bot.servers:
        if server.id not in bot.servers_data:
            add_server(bot, server)

def save_data(bot):
    '''
    Saves the servers data to file.
    '''
    directory = bot.path + "/data"
    write_lock.acquire()
    with open(directory + '/servers.json', 'w') as servers_file:
        json.dump(bot.servers_data, servers_file, indent=4)
    write_lock.release()

