import discord
import logging
import sys

from jshbot.exceptions import BotException, ErrorTypes

def convert_command_blueprints(blueprints):
    '''
    Converts user-friendly(ish) blueprints into the system-friendly version.
    Convert: "?opt1 opt2: ::+"
    To: [[(True, "opt1", False), (False, "opt2", True)], '::+']
    '''
    new_blueprints = []
    required = True
    argument = False
    for blueprint in blueprints:
        split = blueprint.split()
        new_blueprint = [[], '']
        for block in split:
            if block[0] in (':', '^', '&', '+', '#'): # Last part
                new_blueprint[1] = block
                break
            required = block[0] == '?'
            argument = block[-1] == ':'
            block = block.strip('?').strip(':')
            new_blueprint[0].append((required, block, argument))
        new_blueprints.append(new_blueprint)
    return new_blueprints

