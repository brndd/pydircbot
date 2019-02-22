""" The main module of the bot. """

from threading import Thread
import logging
import asyncio
from collections import namedtuple
import sys
import signal

import aioconsole
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
import discord

import pydircbot.irc as irc
import pydircbot.disc as disc


class PyDIRCBot():
    """ The main bot class. """

    def __init__(self, config_manager):
        """ Creates a new bot from the given ConfigManager object. """
        self.config_manager = config_manager
        config = config_manager.config

        #set up our event loop
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.user_input())

        #Handle IRC part of config
        self._twisted_thread = None  #this will contain a handle to the reactor.run() thread later
        icfg = config['irc']
        IRCBotTuple = namedtuple('IRCBotTuple', ('connector', 'factory'))
        self.ircbots = {}
        bot_info = irc.IRCBotInfo(nickname=icfg['nick'], ident=icfg['ident'], realname=icfg['realname'])
        for server, server_info in icfg['servers'].items():
            factory = irc.IRCBotFactory(bot_info, server_info['channels'], server, self)
            #the bots won't *actually* connect until reactor.run()
            connector = reactor.connectTCP(server_info['host'], server_info['port'], factory)
            self.ircbots[server] = IRCBotTuple(connector, factory)

        #Handle Discord part of config
        self._discord_thread = None
        discordloop = asyncio.new_event_loop()
        self.discordbot = disc.DiscordBot(adapter=self, loop=discordloop)

        #Set up the IRC-Discord relay mapping
        #each entry in our channel_mapping has a list of recipients that messages in that channel are forwarded to
        self.channel_mapping = cmap = {}
        for mapping in config['channel_mapping']:
            irc_channel = (mapping['irc_network'], mapping['irc_channel'])
            discord_channel = mapping['discord_channel']
            irc_recipients = cmap.setdefault(irc_channel, list())
            irc_recipients.append(discord_channel)
            discord_recipients = cmap.setdefault(discord_channel, list())
            discord_recipients.append(irc_channel)


    def start(self):
        """ Starts the bot, connecting to IRC and Discord and whatnot.
        Also runs the command line. Blocking. """
        logging.info('Starting bot.')
        #reactor.run() is blocking so we run it in a separate thread
        #if we want the reactor to do something we must use thread-safe methods
        #such as reactor.callFromThread()
        self._twisted_thread = Thread(target=lambda: reactor.run(installSignalHandlers=False), name="twistedthread")
        self._twisted_thread.start()

        #unlike twisted, discord.py uses the common asyncio stuff and can (should) be ran as a task
        #but we'll run it in a thread anyway because it means we need to override discord.py less
        token = self.config_manager.config['discord']['token']
        self._discord_thread = Thread(target=lambda: self.discordbot.run(token), name="discordthread")
        self._discord_thread.start()

        #run our event loop
        windows = sys.platform == 'win32'
        if not windows:
            self.loop.add_signal_handler(signal.SIGINT, self.stop)
            self.loop.add_signal_handler(signal.SIGTERM, self.stop)
        self.loop.run_forever()

    def stop(self):
        """ Cleanly stops all the bots. """
        logging.info('Received command to stop.')
        for server, ircbottuple in self.ircbots.items():
            connector, factory = ircbottuple
            logging.debug('Quitting from IRC server %s', server)
            quitmessage = self.config_manager.config['irc']['quitmessage']
            blockingCallFromThread(reactor, factory.bot.quit, (quitmessage, ))
            logging.debug('Disconnecting IRC connector for %s.', server)
            connector.disconnect()
        logging.debug('Finished disconnecting IRC connectors. Stopping reactor.')
        reactor.stop()
        logging.debug('Stopped reactor.')
        logging.debug('Stopping Discord bot.')
        self.discordbot.stop()
        logging.info('Waiting for Twisted thread to terminate.')
        #wait for threads to terminate... hopefully this will happen.
        self._twisted_thread.join()
        logging.info('Waiting for Discord thread to terminate.')
        self._discord_thread.join()
        logging.debug('Threads have terminated, stopping event loop.')

        #stop our event loop
        self.loop.stop()

    async def user_input(self):
        """ Simple command prompt. """
        while self.loop.is_running():
            try:
                cmd = await aioconsole.ainput("Enter 'quit' to close.\n")
            except EOFError:
                logging.info('Got EOF while reading command, exiting.')
                self.stop()
                break
            except KeyboardInterrupt:
                logging.info('Got KeyboardInterrupt while reading command, exiting.')
                self.stop()
                break
            if cmd == 'quit':
                self.stop()
                break

    def relay_message(self, message):
        """
        Relays the message to all the recipients of the channel it was sent on.
        """
        message_content = str(message)
        i = 0
        for recipient in self._get_recipient_list(message.source):
            #this is a little bad, but it's the best way to figure out where the message is going to
            if isinstance(recipient, int):
                #it's a Discord message so we'll bold the sender
                nick = f"**<{message.simple_sender}>** "
            # elif isinstance(recipient, tuple):
            #     #it's an IRC message. This is commented out because we don't need any special IRC behaviour for now.
            #     pass
            else:
                #it really shouldn't be anything else but this is a safe default
                nick = f"<{message.simple_sender}> "
            self._really_send_message(recipient, nick + message_content)
            i += 1
        if i > 0:
            logging.debug('Relayed message to %d recipients.', i)

    ###############
    #"API" methods#
    ###############
    def _really_send_message(self, target, message):
        """
        This is the function that actually takes the message, figures out whether it's a Discord or an IRC message,
        and then sends it.
        """
        if not isinstance(message, str):
            raise ValueError("Invalid type for 'message'.")

        if isinstance(target, discord.abc.Messageable):
            logging.debug("send_message: sending Discord message via Messageable.")
            coro = target.send(content=message)
            asyncio.run_coroutine_threadsafe(coro, self.discordbot.loop)
        elif isinstance(target, int):
            logging.debug("send_message: sending Discord message via channel ID.")
            channel = self.discordbot.get_channel(target)
            if channel is None:
                raise ValueError(f"Channel {target} not found.")
            coro = channel.send(content=message)
            asyncio.run_coroutine_threadsafe(coro, self.discordbot.loop)
        elif isinstance(target, tuple):
            logging.debug("send_message: sending IRC message via ('server', 'target').")
            server, user = target
            if not server in self.ircbots:
                raise ValueError(f"Server {server} not found.")
            ircbot = self.ircbots[server].factory.bot
            reactor.callFromThread(ircbot.msg, user, message)
        else:
            raise ValueError("Invalid type for 'target'.")

    def _get_recipient_list(self, target):
        """
        Gets the list of recipients for the given target which can be basically all the stuff send_message supports, BUT
        instead of Messageable we only care about channels, not users, so we check for public channel types instead.
        Private channels aren't be supported (for now?).
        """
        if isinstance(target, discord.TextChannel):
            key = target.id
        elif isinstance(target, int):
            key = target
        elif isinstance(target, tuple):
            key = target
        else:
            key = None
        recipients = self.channel_mapping.get(key, list()) #return an empty list by default
        return recipients

    async def send_message(self, target, message):
        """
        Sends message to target as well as all its recipient channels. target can be:
            - a discord.py Messageable object
            - an integer matching a Discord channel ID
            - a tuple ('server', 'target'), where 'server' is an IRC server and 'target' is a channel
              or user on the server
        message is a string.
        """
        #send the message to its intended channel
        self._really_send_message(target, message)
        #send the message to all the recipients of the intended channel
        for recipient in self._get_recipient_list(target):
            self._really_send_message(recipient, message)

    async def send_message_no_relay(self, target, message):
        """
        Sends a message to target but not any of its recipient channels. Otherwise the same as send_message().
        """
        self._really_send_message(target, message)

    ########
    #Events#
    ########

    #Supported event types that can be registered for
    event_listeners = {"MESSAGE_RECEIVED": set()}

    def register_event(self, event_type, listener):
        """ Registers an event listener to listen to an event. """
        if event_type not in self.event_listeners:
            raise ValueError("Invalid event type.")
        self.event_listeners[event_type].add(listener)

    #We're not doing dynamic event registration yet (if ever),
    #all events must be registered before running the bot.
    # def unregister_event(self, event_type, listener):
    #   """ Unregisters an event listener from the given event. """
    #   if event_type not in self.event_listeners:
    #     raise ValueError("Invalid event type.")
    #   self.event_listeners[event_type].discard(listener)

    #actual event callers
    async def message_received(self, message):
        """ Called when a message is received.
        Fires all event listeners listening to the MESSAGE_RECEIVED event.
        message is an object inheriting from adapters.IMessage. """
        self.relay_message(message)
        logging.debug('Firing MESSAGE_RECEIVED listeners.')
        for listener in self.event_listeners["MESSAGE_RECEIVED"]:
            listener(message)
