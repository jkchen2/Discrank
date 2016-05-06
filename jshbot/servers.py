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

def is_mod(bot, server, user_id):
    '''
    Returns true if the given user is a moderator of the given server.
    The server owner and bot owners count as moderators.
    '''
    try:
        moderators = bot.servers_data[server.id]['moderators']
    except KeyError:
        logging.error("Could not find the server {}".format(server_id))
        check_all(bot)
    return user_id in moderators or is_admin(bot, server, user_id)

def is_admin(bot, server, user_id):
    '''
    Returns true if the given user is either the owner of the server or is a
    bot owner.
    '''
    return user_id == server.owner.id or is_owner(bot, user_id)

def is_owner(bot, user_id):
    '''
    Returns true if the given user is one of the bot owners
    '''
    return user_id in bot.configurations['core']['owners']

def get_id(bot, identity, server=None, name=False):
    '''
    Gets the ID number or name of the given identity. Looks through the server
    if it is specified, otherwise it looks through all members the bot can see.
    '''
    if identity.startswith('<@') and identity.endswith('>'):
        identity = identity[2:-1]
    if server:
        members = server.members
    else:
        members = bot.get_all_members()
    result = discord.utils.get(members, name=identity)
    if not result:
        result = discord.utils.get(members, id=identity)

    if result:
        return result.name if name else result.id

    raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
            "{} not found.".format(identity))

def modify_user_group(bot, server, identity, add, which):
    '''
    Add and remove users (either blocked, or moderators) to the servers_data
    dictionary. Throws an error if trying to add and the user is already on the
    list, specified by the which argument.
    '''
    user_id = get_id(bot, identity, server=server)
    which_data = bot.servers_data[server.id][which]
    if add:
        if user_id in which_data:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "User already in the {} list.".format(which))
        bot.servers_data[server.id][which].append(user_id)
    else:
        if user_id not in which_data:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "User was not in the {} list.".format(which))
        bot.servers_data[server.id][which].remove(user_id)

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

