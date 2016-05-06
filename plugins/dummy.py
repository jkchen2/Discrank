import discord

from jshbot.exceptions import ErrorTypes, BotException

def get_commands():
    new_commands = {}
    new_commands['test'] = ([
            'opt: ^',
            '?custom: mand ::+',
            'me +'],[
            ('opt', 'option', 'o'),
            ('custom', 'c')])
    new_shortcuts = {}
    new_shortcuts['opt'] = ('test -opt {} {}', ':^')

    # Command get internally converted from ('?opt:') to (True, 'opt', True)
    # ('opt') to (False, 'opt', False), ('?opt') to (True, 'opt', False), etc.
    # ('?opt1 opt2: opt3') to [(T, 'opt1', F), (F, 'opt2', T), (F, 'opt3', F)]

    return (new_commands, new_shortcuts, None)

def get_response(bot, message, parsed_command, direct):

    response = ''
    tts = False
    message_type = 0
    extra = None
    base, plan_index, options, arguments = parsed_command

    #if base == 'test':
    if plan_index == 0:
        response = "This is the attached argument: " + options['opt'] + '\n'
        response += "Rest of the arguments: " + arguments
    elif plan_index == 1:
        if 'custom' in options:
            response = "The custom option was supplied: " + options['custom'] + '\n'
        response += "The mandatory option is necessary\n"
        response += "You supplied {} arguments: {}".format(len(arguments), str(arguments))
    elif plan_index == 2:
        response = "You have: " + str(arguments)
    else:
        response = "You should never see this"

    return (response, tts, message_type, extra)

