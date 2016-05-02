import discord
import logging
import re

from jshbot import commands
from jshbot.exceptions import BotException, ErrorTypes

# Input: "-create "my tag" -private tag text"
# ['-create', ' ', '"my', ' ', 'tag"', ' ', '-private', ' ', 'tag', ' ', 'text', '-']
# len is 7, want to go from [0, 5]

EXCEPTION = "Parser"

def get_argument_block(split, index, get_all=False):
    #print("Starting from index " + str(index) + ": " + split[index])
    if not split[index] or split[index][0] == ' ': # Unstripped, skip
        return get_argument_block(split, index + 1)
    elif not get_all and split[index][0] == '-': # This is an option
        return None
    elif split[index][0] == '"': # Loop until quote closed
        combined = split[index][1:]
        for it in range(index + 1, len(split) - 1):
            if split[it][-1] == '"' and split[it][-2] != '\\': # Closed
                return (combined + split[it][:-1], it)
            combined += split[it]
        raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                "Detected an unclosed quote", split[index])
    else:
        return (split[index], index) # No loops necessary

def split_parameters(parameters):

    split = re.split('( )', parameters)
    split.append('-')
    print(split)
    pairs = {} # {op1: arg1, op2: arg2} ("op1: op2: +")
    leftover_arguments = [] # [arg3, arg4]
    trailing_arguments = [] # [arg2, arg3, arg4]
    combined_leftover_arguments = '' # arg3 + arg4
    combined_trailing_arguments = '' # arg2 + arg3 + arg4

    in_leftover = False # Looking only for leftover arguments
    last_positional_argument_index = 0
    last_positional_argument = ''
    last_option = ''

    it = 0
    while it < len(split) - 1: # I miss C-like for loops
        if not split[it]: # Skip empty portions
            pass
        elif not in_leftover and split[it][0] == '-': # Option
            argument_block = get_argument_block(split, it + 1)
            last_option = split[it][1:]
            if not argument_block: # Another option was found next
                pairs[last_option] = ''
            else:
                last_positional_argument = argument_block[0]
                last_positional_argument_index = argument_block[1]
                pairs[last_option] = argument_block[0]
                it = argument_block[1] # Update iterator value
        else:
            argument_block = get_argument_block(split, it)
            if argument_block:
                in_leftover = True # Only leftover arguments left
                leftover_arguments.append(argument_block[0])
                it = argument_block[1]
        it += 1

    it = last_positional_argument_index + 1
    if last_positional_argument: # No options
        combined_trailing_arguments += last_positional_argument
    else:
        combined_trailing_arguments += split[0]
    if last_positional_argument:
        trailing_arguments.append(last_positional_argument) # First element
    trailing_arguments += leftover_arguments # Combine lists
    while not split[it] or split[it][0] == ' ': # Get first non-space argument
        combined_trailing_arguments += split[it]
        it += 1
    for it in range(it, len(split) - 1): # Append leftover arguments with spaces
        combined_leftover_arguments += split[it]
    combined_trailing_arguments += combined_leftover_arguments

    arguments = (leftover_arguments,
            trailing_arguments,
            combined_leftover_arguments,
            combined_trailing_arguments)

    # Return split result
    return [pairs, arguments, last_option]

def match_blueprint(options, arguments, last_option, blueprints):
    '''
    '''
    # Command get internally converted from ("?opt:") to (True, "opt", True)
    # ("opt") to (False, "opt", False), ("?opt") to (True, "opt", False), etc.
    # ("?opt1 opt2: opt3") to [(T, "opt1", F), (F, "opt2", T), (F, "opt3", F)]

    # TODO: Consider checking last first?
    
    # Loop through all blueprints
    # Each blueprint is a list of individual plans
    print("List of blueprints: " + str(blueprints))
    print("Current options dictionary: " + str(options))
    for blueprint_index, blueprint in enumerate(blueprints):

        # Represents if the last option with an associated positional argument
        #   is used or not
        no_last_argument = False
        last_option_plan_index = 0
        total_found = 0
        total_required = 0

        # Loop through each plan from a blueprint
        # The plan is a tuple (boolean, string, boolean) that represents
        # (optional, name, argument_required)
        for plan_index, plan in enumerate(blueprint[0]):

            # Check if the option name is in the options dictionary
            # If it is, we can continue. If not, check to see if this is
            #   the last option to be parsed, as there may be overlap in
            #   positional and trailing arguments
            if plan[1] in options:

                if plan[1] == last_option:
                    last_option_plan_index = plan_index

                # Check that the argument_required values match
                # Both must either be True or False
                if plan[2] ^ bool(options[plan[1]]):

                    # Check for the specific arrangement for overlap
                    # There must be no argument, the option must have an
                    #   associated positional argument attached to it, and
                    #   it is the LAST option that was parsed
                    if (not plan[2] and 
                            options[plan[1]] and
                            plan[1] == last_option):
                        no_last_argument = True
                    else:
                        break # Invalid blueprint, required argument mismatch

                total_found += 1

            # Option not found. Check if it is optional
            # If the option is optional, we can skip this option
            else:
                if not plan[0]:
                    break # Invalid blueprint, option not found

        # Matched up the entire list of plans with the options given
        # Now check the trailing argument symbols
        else:

            # Check if number of options don't align
            if total_found < len(options): # Check for extra options
                continue # Not all options were matched

            if not blueprint[0] and len(options) > 0:
                continue # Option number mismatch
            elif not blueprint[0]: # No options, use all arguments
                no_last_argument = True

            # Final check that the last option does or does not require a
            #   positional argument attached to it
            if not no_last_argument and blueprint[0] and options:
                last_plan = blueprint[0][last_option_plan_index]
                if not last_plan[2] and options[last_plan[1]]:
                    no_last_argument = True

            # Get whether or not arguments should be grouped
            group_arguments = blueprint[1] and blueprint[1] in ('^', '&')
            
            # Determine which arguments to use based on no_last_argument and
            #   group_arguments
            arguments_index = 0
            if group_arguments: # Use combined. Either trailing or leftover
                arguments_index = 3 if no_last_argument else 2
            else: # Use separated. Either trailing or leftover
                arguments_index = 1 if no_last_argument else 0

            # Check for the required combined trailing argument
            if not blueprint[1] and arguments[arguments_index]:
                continue # Required no trailing arguments, but found some
            elif (group_arguments and
                    blueprint[1] == '^' and
                    not arguments[arguments_index]):
                continue # Required trailing arguments not found
            elif not group_arguments and blueprint[1]: # Check last arguments
                required_length = len(blueprint[1])
                at_least = blueprint[1][-1] in ('+', '#')
                if blueprint[1][-1] == '#': # Last argument not required
                    required_length -= 1
                list_length = len(arguments[arguments_index])
                # Check lengths
                if not ((list_length == required_length) or
                        (list_length >= required_length and at_least)):
                    continue # Incorrect number of trailing arguments
            elif not blueprint[1] and len(arguments[arguments_index]) > 0:
                continue # Requires no trailing arguments, but found some
                    
            # All criteria satisfied
            return (blueprint_index, no_last_argument, arguments_index)

    # A suitable blueprint could not be found
    raise Exception() # This is probably not the best way to do this

def fill_shortcut(parameters, blueprint, modifiers):
    '''
    Replaces elements in the blueprint with the modifiers specified.
    Example: fill_shortcut('"my tag" tag text', 'tag -create {} {}', ':^')
    Returns: ('tag', '-create "my tag" tag text')
    '''
    
    # Split parameters
    split = re.split('( )', parameters)
    split.append('-')

    it = 0
    format_list = []
    for modifier in modifiers: # :^&+#

        if modifier == ':': # Insert single argument
            block, it = get_argument_block(split, it, get_all=True)
            format_list.append('"' + block + '"')
        else: # Insert remaining trailing arguments
            remaining = ''
            while it < len(split) - 1:
                if modifier in ['^', '&']: # Single
                    remaining += split[it]
                else: # Split
                    block, it = get_argument_block(split, it, get_all=True)
                    remaining += '"' + block + '" '
                it += 1
            format_list.append(remaining.strip())
        it += 1

    # Insert elements from the format list
    filled_blueprint = blueprint.format(*format_list)
    return filled_blueprint.split(' ', 1)

def replace_aliases(pairs, aliases, last_option):
    '''
    Replaces option names in pairs with the corresponding full option name
    in the aliases tuple list
    '''
    if not aliases: # No aliases to parse
        return (pairs, last_option)
    for key in pairs: # Try to find replacements
        for alias in aliases:
            if key in alias:
                if key == last_option:
                    last_option = alias[0]
                pairs[alias[0]] = pairs.pop(key)
    return (pairs, last_option)

def parse(bot, base, parameters, command_pair, shortcut):
    '''
    Parses the given input and returns a touple that contains the base command
    name, the blueprint index it matches, the options/argument dictionary,
    and a list of trailing arguments specified by the blueprint.
    '''
    parameters = parameters.strip() # Safety strip

    if shortcut: # Check blueprint for layout
        try: # TODO: Maybe change this exception handling
            base, parameters = fill_shortcut(
                bot, parameters, command_pair[0], command_pair[1])
        except:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Invalid syntax", bot.commands['syntax'][base])
        command_pair, shortcut = commands.get_command_pair(bot, base)
        return parse(bot, base, parameters, command_pair, shortcut)
    else:
        options, arguments, last_option = split_parameters(parameters)

    # Attempt to replace the option names with ones found by aliases
    # After that, match the options and arguments with a blueprint from the
    #   blueprint list. Due to the iterations during the checks, match_blueprint
    #   also returns the no_last_argument flag, and the index arguments_index
    #   to be used to reference the correct argument type in the arguments
    #   tuple
    try:
        options, last_option = replace_aliases(
                options, command_pair[1], last_option)
        blueprint_index, no_last_argument, arguments_index = match_blueprint(
                options, arguments, last_option, command_pair[0])
    except:
        # Print out the syntax of the command
        raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                "Invalid syntax", bot.commands['syntax'][base])
    
    # Remove positional argument of last option if it exists in the dictionary
    if no_last_argument and last_option in options:
        options[last_option] = ''

    return (base, blueprint_index, options, arguments[arguments_index])

