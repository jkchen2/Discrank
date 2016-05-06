import discord
import random
import socket
import time

from jshbot import servers
from jshbot.exceptions import ErrorTypes, BotException

EXCEPTION = 'Base'

def get_commands():
    '''
    Sets up new commands and shortcuts in the proper syntax.
    See command_reference.txt for more information and examples
    See dummy.py for a complete sample reference
    '''
    commands = {}
    shortcuts = {}
    manual = {}

    commands['ping'] = (['&'], [])
    commands['debug'] = ([
        'plugin:', 'plugin list', 'eval ^', 'latency'],[
        ('plugin', 'p'), ('list', 'l'), ('eval', 'evaluate', 'python', 'py'),
        ('latency', 'ping')])
    commands['owner'] = ([
        'halt', 'restart', 'ip', 'backup'],[])
    commands['mod'] = ([
        'info', 'block:', 'unblock:', 'clear', 'add:', 'remove:'],[
        ('info', 'i'), ('clear', 'c')])
    commands['base'] = ([
        'version', 'source', 'uptime', 'help: ?topic:'],[
        ('version', 'ver', 'v'), ('source', 'src', 'git'), ('help', 'h')])

    shortcuts['clear'] = ('mod -clear', '')
    shortcuts['help'] = ('base -help {}', '^')

    manual['ping'] = {
        'description': 'Command to ping the bot for a response.',
        'usage': [
            ('(argument)', 'Optional argument.')]}
    manual['debug'] = {
        'description': 'Debug commands.',
        'usage': [
            ('-plugin <plugin>', 'Show information about the plugin.'),
            ('-plugin -list', 'Lists all active plugins.'),
            ('-eval <expression>', 'Evaluates the given expression.'),
            ('-latency', 'Gets ping time to current server.')],
        'other': 'Be careful with these commands! They can break the bot.'}
    manual['owner'] = {
        'description': 'Commands for the owner only.',
        'usage': [
            ('-halt', 'Stops the bot.'),
            ('-restart', 'Restarts the bot.'),
            ('-ip', 'Gets the internal IP address of the bot.'),
            ('-backup', 'Sends each owner a copy of the bot data files.'),]}
    manual['mod'] = {
        'description': 'Commands for server bot moderators.',
        'usage': [
            ('-info', 'Gets server information.'),
            ('-block <user>', 'Blocks the user from bot interaction.'),
            ('-unblock <user>', 'Unblocks the user from bot interaction.'),
            ('-clear', 'Pushes chat upwards.'),
            ('-add <user>', 'Adds the user to the moderators list.'),
            ('-remove <user>', 'Removes the user from the moderators list.')],
        'shorcuts': [('clear', '-clear')]}
    manual['base'] = {
        'description': 'Base commands.',
        'usage': [
            ('-version', 'Gets the bot version and date.'),
            ('-source', 'Gets the github link to the source of JshBot.'),
            ('-uptime', 'Gets how long the bot has been up.'),
            ('-help <command> (-topic <index>)', 'Gets the help about the '
                'given command, with extra information on a specific option '
                'if the topic option is provided with a valid index.')],
        'shortcuts': [('help <arguments>', '-help <arguments>')]}

    return (commands, shortcuts, manual)

def get_response(bot, message, parsed_command, direct):

    response = ''
    tts = False
    message_type = 0
    extra = None
    base, plan_index, options, arguments = parsed_command

    if base == 'ping':
        response = 'Pong!\n' + arguments

    elif base == 'base':
        if plan_index == 0: # version
            response = '`{}`\n{}'.format(bot.version, bot.date)
        elif plan_index == 1: # source
            response += random.choice([
                "It's shit. I'm sorry.",
                "You want to see what the Matrix is like?",
                "Script kiddie level stuff in here.",
                "Beware the lack of PEP 8 guidelines inside!",
                "Snarky comments inside and out.",
                "Years down the road, this will all just be a really "
                "embarrassing but funny joke.",
                "Made with ~~love~~ pure hatred.",
                "At least he's using version control."])
            response += "\nhttps://github.com/jkchen2/JshBot"
        elif plan_index == 2: # uptime
            uptime_total_seconds = int(time.time()) - bot.time
            uptime_struct = time.gmtime(uptime_total_seconds)
            days = int(uptime_total_seconds / 86400)
            hours = uptime_struct.tm_hour
            minutes = uptime_struct.tm_min
            seconds = uptime_struct.tm_sec
            response = ("The bot has been on since **{initial}**\n{days} "
            "days\n{hours} hours\n{minutes} minutes\n{seconds} "
            "seconds").format(initial=bot.readable_time, days=days, 
                    hours=hours, minutes=minutes, seconds=seconds)
        elif plan_index == 3: # help
            response = get_help(bot, options['help'], 
                    topic=options['topic'] if 'topic' in options else None)

    elif base == 'mod':
        if servers.is_mod(bot, message.server, message.author.id):
            if plan_index == 0: # info
                server_data = bot.servers_data[message.server.id]
                response = ('```\n'
                'Information for server {0}\n'
                'Owner: {1}\n'
                'Moderators: {moderators}\n'
                'Blocked users: {blocked}\n'
                'Muted: {muted}\n'
                'Muted channels: {muted_channels}\n```').format(
                        message.server, message.server.owner.id, **server_data)
            elif plan_index in (1, 2): # block or unblock
                add = plan_index == 1
                identity = (options['block'] if add else options['unblock'])
                servers.modify_user_group(bot, message.server,
                        identity, add, 'blocked')
                name = servers.get_id(bot, identity, message.server, True)
                response = '{} is {} blocked'.format(name,
                        'now' if add else 'no longer')
            elif plan_index == 3: # clear
                response = '```\n'
                for i in range(0, 80):
                    response += '.\n'
                response += random.choice([
                "Think twice before scrolling up.",
                "clear ver {}".format(bot.version),
                "Can you find the one comma?",
                "Are people watching? If so, best not to scroll up.",
                "Don't worry, just censorship doing its thing.",
                "This is why we can't have nice things.",
                "The only one who can spam is ME.",
                "That made me feel a bit queasy...",
                "We need a better content filter. 18+ checks, maybe?",
                "You ANIMALS. At least I'm not one.",
                "Scroll up if you want to be on a list.",
                "I'll bet the NSA will have a fun time scrolling up.",
                "So much wasted space...", 
                "This is pretty annoying, huh? Well TOO BAD.",
                "No time to delete!"])
                response += '```\n'
            elif plan_index >= 4: # add or remove
                if servers.is_admin(bot, message.server, message.author.id):
                    add = plan_index == 4
                    identity = (options['add'] if add else options['remove'])
                    servers.modify_user_group(bot, message.server,
                            identity, add, 'moderators')
                    name = servers.get_id(bot, identity, message.server, True)
                    response = '{} is {} a moderator'.format(name,
                            'now' if add else 'no longer')
                else:
                    raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                            "You must be an admin to use these commands.")
        else:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "You must be a moderator to use these commands.")

    elif base == 'owner':
        if message.author.id in bot.configurations['core']['owners']:

            if plan_index == 0: # halt
                bot.interrupt_say(
                        None, "Going down...", channel=message.channel)
                bot.shutdown()
            elif plan_index == 1: # restart
                bot.interrupt_say(
                        None, "Restarting...", channel=message.channel)
                bot.restart()
            elif plan_index == 2: # ip
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80)) # Thanks Google, you da real MVP
                ip = s.getsockname()[0]
                s.close()
                response = "Local IP: " + ip
            elif plan_index == 3: # backup
                response = "I haven't even written a save server data function yet!"
        else:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "You must be the bot owner to use these commands.")

    elif base == 'debug':
        response = "You get the point: " + str(parsed_command)
            
    else:
        response = "Your command was: " + base

    return (response, tts, message_type, extra)

def get_help(bot, base, topic=None):
    '''
    Gets the help of the base command, or the specific topic of a help command.
    '''
    if base not in bot.manual:
        return "No help entry for this command."
    manual_entry = bot.manual[base]
    invoker = bot.configurations['core']['command_invokers'][0]

    # Handle specific topic help
    if topic:
        try:
            topic_index = int(topic)
        except:
            return "Topic number is not a valid integer."
        if 'usage' not in manual_entry:
            return "No usage entry for this command."
        elif topic_index < 1 or topic_index > len(manual_entry['usage']):
            return "Invalid topic index."
        else:
            topic_pair = manual_entry['usage'][topic_index - 1]
            return '```\n{}{} {}\n\t{}```'.format(
                    invoker, base, topic_pair[0], topic_pair[1])
    
    # Handle regular help
    # Description, usage, aliases, shortcuts, other
    aliases = bot.commands[base][0][1]
    response = '```\n'
    if 'description' in manual_entry:
        response += 'Description:\n\t{}\n\n'.format(manual_entry['description'])
    if 'usage' in manual_entry:
        response += 'Usage: {}{} (syntax)\n'.format(invoker, base)
        for topic_index, topic in enumerate(manual_entry['usage']):
            response += '\t({}) {}\n'.format(topic_index + 1, topic[0])
        response += '\n'
    if aliases:
        response += 'Aliases:\n'
        print(aliases)
        for alias in aliases:
            response += '\t{}:'.format(alias[0])
            for name in alias[1:]:
                response += ' {},'.format(name)
            response = response[:-1] + '\n'
        response += '\n'
    if 'shortcuts' in manual_entry:
        response += 'Shortcuts:\n'
        for shortcut in manual_entry['shortcuts']:
            response += '\t{}{}\n\t\t{}{} {}\n'.format(
                    invoker, shortcut[0], invoker, base, shortcut[1])
        response += '\n'
    if 'other' in manual_entry:
        response += 'Other information:\n\t{}\n'.format(manual_entry['other'])

    return response + '```'

def get_usage_reminder(bot, base):
    '''
    Returns the usage syntax for the base command (simple format).
    '''
    if base not in bot.manual or 'usage' not in bot.manual[base]:
        return "No usage entry for this command."
    response = '```\n'
    invoker = bot.configurations['core']['command_invokers'][0]
    response += 'Usage: {}{} (syntax)\n'.format(invoker, base)
    for topic_index, topic in enumerate(bot.manual[base]['usage']):
        response += '\t({}) {}\n'.format(topic_index + 1, topic[0])
    response += '```'
    return response

