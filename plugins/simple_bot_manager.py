import discord
import asyncio
import os.path
import urllib.request
import random


from jshbot.exceptions import ErrorTypes, BotException

__version__ = '0.1.0'
EXCEPTION = 'Simple bot manager'

def get_commands():
    commands = {}
    shortcuts = {}
    manual = {}

    commands['botman'] = ([
        'change ?avatar ?status', 'nick &', 'name ^', 'status &', 'avatar &'],[
        ('change', 'c'), ('avatar', 'a'), ('status', 's')])

    manual['botman'] = {
        'description': 'Simple bot manager. Allows you to change the name, '
            'status, and avatar of the bot in-chat.',
        'usage': [
            ('-change (-avatar) (-status)', 'Changes to a random avatar, '
                'status, or both from the list in the data directory.'),
            ('-nick (nickname)', 'Changes the nickname of the bot. To clear '
                'the nickname, do not enter one.'),
            ('-name <name>', 'Changes the name of the bot. Limit of 20 '
                'characters. Limited to 2 changes per hour.'),
            ('-status (status)', 'Changes the status of the bot. To clear '
                'the status, do not enter one.'),
            ('-avatar (URL)', 'Changes the avatar of the bot with the given '
                'URL. To clear the avatar, do not enter a URL.')],
        'other': 'Only bot moderators can use these commands.'}

    return (commands, shortcuts, manual)

def get_random_line(bot, name):
    '''
    Gets a random line in the file given by the name argument.
    '''
    file_path = bot.path + '/data/simple_bot_manager.py/' + name
    try:
        if os.stat(file_path).st_size > 0:
            with open(file_path, 'r') as data_file:
                return str(random.choice(list(data_file))).rstrip()
        else:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "The {} file is empty.".format(name))
    except:
        raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                "The {} file was not found.".format(name))

async def get_response(bot, message, parsed_command, direct):

    response = ''
    tts = False
    message_type = 0
    extra = None
    base, plan_index, options, arguments = parsed_command

    if plan_index == 0: # Change avatar, status, or both

        if len(options) == 0:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Either the avatar, status, or both flags must be used.")

        if 'avatar' in options:
            url = get_random_line(bot, 'avatars.txt')
            try: # Try to change the avatar
                avatar_bytes = urllib.request.urlopen(url).read()
                await bot.edit_profile(bot.get_token(), avatar=avatar_bytes)
            except Exception as e:
                raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                        "Failed to update the avatar.", e=e)
        if 'status' in options:
            try:
                status = get_random_line(bot, 'statuses.txt')
                await bot.change_status(discord.Game(name=status))
            except Exception as e:
                raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                        "Failed to update the status.", e=e)

    elif plan_index == 1: # Change nickname
        try:
            await bot.change_nickname(
                    message.server.me, arguments if arguments else None)
        except Exception as e:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Failed to change the nickname.", e=e)
    elif plan_index == 2: # Change name
        if len(arguments) > 20:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Name is longer than 20 characters.")
        try:
            await bot.edit_profile(bot.get_token(), username=arguments)
        except Exception as e:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Failed to update the name.", e=e)
    elif plan_index == 3: # Change status
        try:
            await bot.change_status(
                    discord.Game(name=arguments) if arguments else None)
        except Exception as e:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Failed to update the status.", e=e)
    elif plan_index == 4: # Change avatar
        try:
            avatar_bytes = urllib.request.urlopen(arguments).read()
            await bot.edit_profile(bot.get_token(), avatar=avatar_bytes)
        except Exception as e:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Failed to update the avatar.", e=e)
    
    response = "Bot stuff updated!"

    return (response, tts, message_type, extra)


