import discord
import logging
import sys

from jshbot.exceptions import BotException, ErrorTypes

EXCEPTION = 'Commands'

def convert_plans(plans):
    '''
    Converts user-friendly(ish) plans into the system-friendly version.
    Convert: "?opt1 opt2: ::+"
    To: [[(True, "opt1", False), (False, "opt2", True)], '::+']
    Convert: "*"
    To: [[], '*']
    '''
    new_plans = []
    required = True
    argument = False
    for plan in plans: # Convert each individual plan
        split = plan.split()
        new_plan = [[], '']
        for block in split: # Parse each option
            if block[0] in (':', '^', '&', '+', '#'): # Last part
                new_plan[1] = block
                break
            required = block[0] == '?'
            argument = block[-1] == ':'
            block = block.strip('?').strip(':')
            new_plan[0].append((required, block, argument))
        new_plans.append(new_plan)
    return new_plans

def add_commands(bot, new_commands, plugin):
    '''
    Checks that all keys in the new dictionary are unique from those in the old
    dictionary. If all keys are good, add them to the bot commands dictionary.
    '''
    # No shortcuts
    if not new_commands:
        return

    # Check that there are no command name collisions
    for key in new_commands:
        is_shortcut = type(new_commands[key][0]) is str
        if key in bot.commands:
            raise BotException(ErrorTypes.FATAL, EXCEPTION,
                    "Attempting to add a command that already exists", key)
        if is_shortcut:
            bot.commands[key] = new_commands[key]
        else:
            new_plans = convert_plans(new_commands[key][0]) # Convert and add
            bot.commands[key] = ((new_plans, new_commands[key][1]), plugin)

def add_manual(bot, manual):
    '''
    Adds the manual entries to the bot manual dictionary.
    '''
    # Do practically the same thing for manual entries
    if not manual: # No manual entry :c
        return
    
    for key in manual:
        if key in bot.manual:
            raise BotException(ErrorTypes.FATAL, EXCEPTION,
                    "Attempting to add a manual entry that already exists", key)
        else:
            bot.manual[key] = manual[key]

def get_command_pair(bot, base):
    '''
    Returns a touple of the command pair with the given base and whether or not
    it is a shortcut.
    '''
    try:
        is_shortcut = type(bot.commands[base][0]) is str
        if is_shortcut:
            command_pair = bot.commands[base]
        else:
            command_pair = bot.commands[base][0]
        return (command_pair, is_shortcut)
    except KeyError:
        return (None, None)


def execute(bot, message, parsed_command):
    '''
    Gets the proper response for the parsed command by first getting the plugin,
    then calling the get_response function associated with that plugin.
    '''
    # Get plugin
    base = parsed_command[0]
    plugin_name = bot.commands[base][1]
    plugin = bot.plugins[plugin_name]

    # Execute plugin's get_response
    return plugin.get_response(bot, message, parsed_command)








