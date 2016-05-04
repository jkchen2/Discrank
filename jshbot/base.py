import discord

from jshbot import configurations, servers
from jshbot.exceptions import ErrorTypes, BotException

def get_commands():
    '''
    Sets up new commands and shortcuts in the proper syntax
    '''
    new_commands = {}
    new_commands['ping'] = (['&'], []) # Wild card
    new_commands['debug'] = ([
            'plugin:', # Options
            'plugin list',
            'eval ^',
            'latency'],[
            ('plugin', 'p'), # Aliases
            ('list', 'l'),
            ('eval', 'evaluate', 'python', 'py'),
            ('latency', 'ping')])
    new_commands['owner'] = ([
            'halt', # Options
            'restart',
            'add:',
            'remove:',
            'ip',
            'backup'],[]) # No aliases
    new_commands['mod'] = ([
            'info', # Options
            'block:',
            'unblock:',
            'clear'],[
            ('info', 'i'), # Aliases
            ('clear', 'c')])
    new_commands['base'] = ([
            'version', # Options
            'source',
            'uptime',
            'help :'],[
            ('version', 'ver', 'v'), # Aliases
            ('source', 'src', 'git'),
            ('help', 'h')])
    new_commands['tag'] = ([
            'create: ?sound ?private ^',
            'create: ?sound ?private random +',
            'info: ?date ?user',
            'list ?user:',
            'search ^'],[
            ('create', 'c'),
            ('info', 'i'),
            ('list', 'l'),
            ('search', 'find', 's')])
    new_shortcuts = {}
    new_shortcuts['clear'] = ('mod -clear', '')
    new_shortcuts['help'] = ('base -help {}', '^')
    new_shortcuts['tc'] = ('tag -create {} {}', ':^')

    # Command get internally converted from ('?opt:') to (True, 'opt', True)
    # ('opt') to (False, 'opt', False), ('?opt') to (True, 'opt', False), etc.
    # ('?opt1 opt2: opt3') to [(T, 'opt1', F), (F, 'opt2', T), (F, 'opt3', F)]

    # TODO: Test the test commands and shortcuts
    # Example command: 'tag -create 'my tag' tag text
    # Blueprint: 'create: private ^'
    # Shortcut blueprint: ['tc'] = ('tag -create {} {}', ':^')

    print("Commands: " + str(new_commands))
    print("Shortcuts: " + str(new_shortcuts))

    return (new_commands, new_shortcuts)

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
            response = "You requested help about this: " + arguments[0]

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
        pass

    elif base == 'debug':
        response = "You get the point: " + str(parsed_command)

    elif base == 'tag':
        if plan_index <= 1: # create tag (maybe random)
            response = "Tag name: " + options['create'] + '\n'
            if 'sound' in options:
                response += "...and it's a soundtag\n"
            if 'private' in options:
                response += "...and it's a private tag\n"
            if plan_index == 0: # Not random
                response += "The tag will say: " + arguments + '\n'
            else: # Random
                response += "The tag will have text with these choices:\n"
                response += str(arguments)
        elif plan_index == 2: # info
            response = "Tag info on: " + options['info'] + '\n'
            if 'date' in options:
                response += "You want the date it was created"
            if 'user' in options:
                response += "You want the user who created it"
        elif plan_index == 3: # list
            if 'user' in options:
                response += "List tags made by: " + options['user']
            else:
                response += "list all tags"
        elif plan_index == 4: # search
            response += "Search tags with keyword: " + arguments
            
    else:
        response = "Your command was: " + base

    return (response, tts, message_type, extra)







