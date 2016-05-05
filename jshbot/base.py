import discord

from jshbot import configurations, servers
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
        'halt', 'restart', 'add:', 'remove:', 'ip', 'backup'],[])
    commands['mod'] = ([
        'info', 'block:', 'unblock:', 'clear'],[
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
            ('-add <user>', 'Adds the user to the moderators list.'),
            ('-remove <user>', 'Removes the user from the moderators list.'),
            ('-ip', 'Gets the internal IP address of the bot.'),
            ('-backup', 'Sends each owner a copy of the bot data files.'),]}
    manual['mod'] = {
        'description': 'Commands for server bot moderators.',
        'usage': [
            ('-info', 'Gets server information.'),
            ('-block <user>', 'Blocks the user from bot interaction.'),
            ('-unblock <user>', 'Unblocks the user from bot interaction.'),
            ('-clear', 'Pushes chat upwards.')],
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
        'shortcuts': [('help <arguments>', '-help -topic <arguments>')]}

    return (commands, shortcuts, manual)

def get_response(bot, message, parsed_command):

    response = ''
    tts = False
    message_type = 0
    extra = None
    base, plan_index, options, arguments = parsed_command

    if base == 'ping':
        response = 'Pong!\n' + arguments

    elif base == 'base':
        if plan_index == 0: # version
            response = "(Version) This is some information text"
        elif plan_index == 1: # source
            response = "https://github.com/jkchen2/JshBot"
        elif plan_index == 2: # uptime
            response = "Bot has been up since forever ago"
        elif plan_index == 3: # help
            response = "You requested help about this: " + options['help'] + '\n'
            if 'topic' in options:
                response += "You want specific information at: " + options['topic']

    elif base == 'mod':
        if plan_index == 0: # info
            response = "This is the info command!"
        elif plan_index == 1: # block
            response = "You're trying to block: " + options['block']
        elif plan_index == 2: # unblock
            response = "You're trying to unblock: " + options['unblock']
        elif plan_index == 3: # clear
            response = "Pretend there is a lot of text here."

    elif base == 'owner':
        if message.author.id in bot.configurations['core']['owners']:

            if plan_index == 0: # halt
                response = "You can't stop this train"
            elif plan_index == 1: # restart
                response = "You can't restart this train"
            elif plan_index == 2: # add
                response = "You're trying to add an admin: " + options['add']
            elif plan_index == 3: # remove
                response = "You're trying to remove an admin: " + options['remove']
            elif plan_index == 4: # ip
                response = "192.168.something.something"
            elif plan_index == 5: # backup
                response = "I haven't even written a save server data function yet!"
        else:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "You must be the bot owner to use these commands.")

    elif base == 'debug':
        response = "You get the point: " + str(parsed_command)
            
    else:
        response = "Your command was: " + base

    return (response, tts, message_type, extra)

def get_usage_reminder(bot, base):
    response = 'Help is currently being developed\n```'
    response += str(bot.manual[base]) + '```'
    return response
