import discord

from jshbot import configurations, servers

'''
'''

def get_commands():
    '''
    Sets up new commands and shortcuts in the proper syntax
    '''
    new_commands = {}
    new_commands["ping"] = (["*"]) # Wild card
    new_commands["admin"] = ([
            "halt", # Options
            "restart",
            "ip",
            "backup"],[]) # No aliases
    new_commands["mod"] = ([
            "info", # Options
            "add:",
            "remove:",
            "block:",
            "unblock:",[
            ("info", "i"), # Aliases
            ("clear", "c")])
    new_commands["base"] = ([
            "version", # Options
            "source",
            "uptime"],[
            ("version", "ver", "v"), # Aliases
            ("source", "src", "git")])
    new_shortcuts = {}
    new_shortcuts["clear"] = ("mod -clear", "")

    # Command get internally converted from ("?opt:") to (True, "opt", True)
    # ("opt") to (False, "opt", False), ("?opt") to (True, "opt", False), etc.
    # ("?opt1 opt2: opt3") to [(T, "opt1", F), (F, "opt2", T), (F, "opt3", F)]

    # TODO: Test the test commands and shortcuts
    # Example command: "tag -create "my tag" tag text
    # Blueprint: "create: private ^"
    # Shortcut blueprint: ["tc"] = ("tag -create {} {}", ":^")

    return (new_commands, new_shortcuts)
