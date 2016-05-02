import asyncio
import discord
import logging
import os.path

from jshbot import configurations, plugins, commands
from jshbot.exceptions import BotException

class Bot(discord.Client):
    
    def __init__(self):
        logging.debug("=== Starting up JshBot {} ===".format(self.version))
        logging.debug("=== Time: {} ===".format(time.strftime("%s")))
        super().__init__()

        self.path = os.path.split(os.path.realpath(__file__))[0][:-7]
        logging.debug("Setting directory to {}".format(path));

        logging.debug("Loading configurations...")
        self.configurations = configurations.get_configurations(self)
        logging.debug("Loading plugins...")
        self.plugins = plugins.get_plugins(self)
        logging.debug("Loading commands...")
        self.commands = commands.get_commands(self)
        logging.debug("Loading server data...")
        self.servers_data = servers.get_servers_data(self)

        # Extras
        self.edit_dictionary = []
    
    def get_token():
        return self.configurations['core']['token']

    def can_respond(message):
        '''
        Determines whether or not the bot can respond to the given message.
        Checks that the message has text, matches an invoker, and that the
        server/channel/user is not muted or blocked. Admins/moderators override.
        '''
        author = message.author
        server_data = self.servers[message.server.id]

        if (not message.content or 
                message.content[0] not in configurations['core']['invokers']):
            return False

        try:
            # Owners/moderators override everything
            channel_id = message.channel.id
            if (author in self.configurations['core']['owners']) or
                    (author in server_data['moderators']):
                return True
            # Server/channel muted, or user is blocked
            if (server_data['muted']) or
                    (channel_id in server_data['muted_channels']) or
                    (author in server_data['blocked']):
                return False
        except KeyError: # Bot may not have updated fast enough
            logging.warn("Failed to find server in can_respond()")
            servers.check_all(self)
            return can_respond(message)

        return True # Clear to respond

    async def on_message(self, message):
        plugins.on_message_broadcast(self, message)

        # Ensure bot can respond properly
        if not can_respond(message):
            return

        # Ensure command is valid
        split_content = message.content[1:].split(' ', 1)
        if len(split_content) == 1: # No spaces
            return
        base, parameters = split_content
        blueprints, shortcut = commands.get_blueprints(self, base)
        if not blueprints: # Suitable command not found
            return

        # Bot is clear to get response. Send typing to signify
        if self.configurations['core']['send_typing']:
            await client.send_typing(message.channel)

        # Parse command and reply
        try:
            parsed_command = parser.parse(
                    self, base, parameters, blueprints, shortcut)
            response = commands.execute(self, message, parsed_command)
        except BotException as e: # Respond with error message
            response = (str(e), False)
        message_reference = await client.send_message(
                message.channel, response[0], tts=response[1])

        # A response looks like this:
        # (text, tts, message_type, extra)
        # message_type can be:
        # 0 - normal
        # 1 - permanent
        # 2 - terminal (deletes itself after 'extra' seconds)
        # 3 - active (pass the reference back to the plugin to edit)
        # If message_type is >= 1, do not add to the edit dictionary
        # TODO: Add normal message response to the edit dictionary
        

    async def on_ready(self):
        plugins.on_ready_broadcast(self)

        #logging.debug("Setting bot name...")
        # Set bot name

        logging.debug("=== {} online ===".format(self.user.name))

bot = Bot()
bot.run(bot.get_token())
