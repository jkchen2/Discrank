import asyncio
import discord
import logging
import os.path
import time
import sys
import os

from jshbot import configurations, plugins, commands, servers, parser
from jshbot.exceptions import ErrorTypes, BotException

EXCEPTION = 'Core'

class Bot(discord.Client):
    
    def __init__(self, debug):
        self.version = '0.3.0-alpha'
        self.date = 'May 6th, 2016'
        self.time = int(time.time())
        self.readable_time = time.strftime('%c')
        self.debug = debug

        if self.debug:
            logging.debug("=== Starting up JshBot {} ===".format(self.version))
            logging.debug("=== Time: {} ===".format(self.readable_time))
        else:
            print("=== Starting up JshBot {} ===".format(self.version))
            print("=== Time: {} ===".format(self.readable_time))

        super().__init__()

        self.path = os.path.split(os.path.realpath(__file__))[0][:-7]
        logging.debug("Setting directory to {}".format(self.path));

        logging.debug("Loading configurations...")
        self.configurations = configurations.get_configurations(self)
        logging.debug("Loading plugins and commands...")
        self.commands = {}
        self.manual = {}
        self.plugins = plugins.get_plugins(self)
        logging.debug("Loading server data...")
        self.servers_data = servers.get_servers_data(self)

        # Extras
        self.edit_dictionary = {}

    def interrupt_say(self, channel_id, message, channel=None):
        '''
        Allows plugins to send messages without having to return directly from
        get_response. This should mostly be avoided, and just used for errors
        or other immediately relevant notifications.
        '''
        if not channel:
            try:
                channel = discord.utils.get(
                        self.get_all_channels(), id=channel_id)
            except:
                raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                        "Server {} could not be found.".format(server_id))
        asyncio.ensure_future(self.send_message(channel, message))
    
    def get_token(self):
        return self.configurations['core']['token']

    def usage_reminder(self, base):
        '''
        Uses the base module to get the usage reminder for a command.
        '''
        base_module = self.plugins['base'][0]
        return base_module.get_usage_reminder(self, base)

    def can_respond(self, message):
        '''
        Determines whether or not the bot can respond to the given message.
        Checks that the message has text, matches an invoker, and that the
        server/channel/user is not muted or blocked. Admins/moderators override.
        '''
        if (not message.content or 
                message.content[0] not in 
                    self.configurations['core']['command_invokers']):
            return False

        author_id = message.author.id
        server_data = self.servers_data[message.server.id]

        try:
            # Owners/moderators override everything
            channel_id = message.channel.id
            if ((author_id in self.configurations['core']['owners']) or
                    (author_id in server_data['moderators'])):
                return True
            # Server/channel muted, or user is blocked
            if ((server_data['muted']) or
                    (channel_id in server_data['muted_channels']) or
                    (author_id in server_data['blocked'])):
                return False
        except KeyError as e: # Bot may not have updated fast enough
            logging.warn("Failed to find server in can_respond(): " + str(e))
            servers.check_all(self)
            time.sleep(5) # remove later
            return self.can_respond(message)

        return True # Clear to respond

    async def on_message(self, message):
        plugins.broadcast_event(self, 2, message)

        # Ensure bot can respond properly
        if not self.can_respond(message):
            return

        # Ensure command is valid
        split_content = message.content[1:].split(' ', 1)
        if len(split_content) == 1: # No spaces
            split_content.append('')
        base, parameters = split_content
        command_pair, shortcut = commands.get_command_pair(self, base)
        if not command_pair: # Suitable command not found
            logging.debug("Suitable command not found: " + base)
            return

        # Bot is clear to get response. Send typing to signify
        if self.configurations['core']['send_typing']:
            await self.send_typing(message.channel)

        # Parse command and reply
        try:
            print(message.author.name + ': ' + message.content)
            parsed_command = parser.parse(
                    self, base, parameters, command_pair, shortcut)
            print('\t' + str(parsed_command))
            response = await (commands.execute(self, message, parsed_command))
        except BotException as e: # Respond with error message
            response = (str(e), False, 0, None)
        message_reference = await self.send_message(
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
        plugins.broadcast_event(self, 0)

        # Make sure server data is ready
        servers.check_all(self)

        #logging.debug("Setting bot name...")
        # Set bot name

        if self.debug:
            logging.debug("=== {} online ===".format(self.user.name))
        else:
            print("=== {} online ===".format(self.user.name))

    async def on_error(self, event, *args, **kwargs):
        plugins.broadcast_event(self, 1, event, *args, **kwargs)
    async def on_socket_raw_receive(self, msg):
        plugins.broadcast_event(self, 3, msg)
    async def on_socket_raw_send(self, payload):
        plugins.broadcast_event(self, 4, payload)
    async def on_message_delete(self, message):
        plugins.broadcast_event(self, 5, message)
    async def on_message_edit(self, before, after):
        plugins.broadcast_event(self, 6, before, after)
    async def on_channel_delete(self, channel):
        plugins.broadcast_event(self, 7, channel)
    async def on_channel_create(self, channel):
        plugins.broadcast_event(self, 8, channel)
    async def on_channel_update(self, before, after):
        plugins.broadcast_event(self, 9, before, after)
    async def on_member_join(self, member):
        plugins.broadcast_event(self, 10, member)
    async def on_member_update(self, before, after):
        plugins.broadcast_event(self, 11, before, after)
    async def on_server_join(self, server):
        plugins.broadcast_event(self, 12, server)
    async def on_server_remove(self, server):
        plugins.broadcast_event(self, 13, server)
    async def on_server_update(self, before, after):
        plugins.broadcast_event(self, 14, before, after)
    async def on_server_role_create(self, server, role):
        plugins.broadcast_event(self, 15, server, role)
    async def on_server_role_delete(self, server, role):
        plugins.broadcast_event(self, 16, server, role)
    async def on_server_role_update(self, before, after):
        plugins.broadcast_event(self, 17, before, after)
    async def on_server_available(self, server):
        plugins.broadcast_event(self, 18, server)
    async def on_server_unavailable(self, server):
        plugins.broadcast_event(self, 19, server)
    async def on_voice_state_update(self, before, after):
        plugins.broadcast_event(self, 20, before, after)
    async def on_member_ban(self, member):
        plugins.broadcast_event(self, 21, member)
    async def on_member_unban(self, server, user):
        plugins.broadcast_event(self, 22, server, user)
    async def on_typing(self, channel, user, when):
        plugins.broadcast_event(self, 23, channel, user, when)


    # TODO: Add other plugin broadcast events

    def save_data(self):
        '''
        Saves all data. For now, this will just be the servers file.
        '''
        logging.debug("Saving data...")
        servers.save_data(self)
        logging.debug("Saving data complete.")

    def restart(self):
        logging.debug("Attempting to restart the bot...")
        self.save_data()
        os.execv(self.path + '/start.py', sys.argv)

    def shutdown(self):
        logging.debug("Writing data on shutdown...")
        self.save_data()
        logging.debug("Closing down!")
        sys.exit()

def initialize(debug=False):
    if debug:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    bot = Bot(debug)
    bot.run(bot.get_token())
    logging.error("Bot disconnected. Shutting down...")
    bot.shutdown()

