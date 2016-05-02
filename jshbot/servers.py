import asyncio
import discord
import logging
import os.path

def get_servers_data(bot):
    directory = bot.path + "/data"
    try:
        with open(bot_directory + '/servers.json', 'r') as servers_file:
            return json.load(servers_file)
    except:
        logging.error("Could not open the servers data file")

def add_server(bot, server):
    # NOTE: Can't use sets because they aren't JSON serializable :c
    bot.servers_data[server.id] = {
            'muted':False,
            'muted_channels':{},
            'moderators':{},
            'blocked':{}
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

