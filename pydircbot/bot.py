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

import pydircbot.irc as irc
import pydircbot.disc as disc


class PyDIRCBot():
    """ The main bot class. """

    def __init__(self, config):
        """ Creates a new bot from the given config object. """
        self.config = config

        #set up our event loop
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.user_input())

        #Handle IRC part of config
        self._twisted_thread = None  #this will contain a handle to the reactor.run() thread later
        icfg = config.config['irc']
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
        #but we'll run it in a thread anyway because it means we need to modify discord.py less
        token = self.config.config['discord']['token']
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
            quitmessage = self.config.config['irc']['quitmessage']
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

    ###############
    #"API" methods#
    ###############
    async def send_message(self, target, message):
        """
        Sends message to target. target can be:
            - a discord.py Messageable object
            - an integer matching a Discord channel ID
            - a tuple ('server', 'target'), where 'server' is an IRC server and 'target' is a channel
              or user on the server
        message is a string.
        """
        from discord.abc import Messageable

        if not isinstance(message, str):
            raise ValueError("Invalid type for 'message'.")

        if isinstance(target, Messageable):
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
        Fires all event listeners listening to the MESSAGE_RECEIVED event. """
        logging.debug('Firing MESSAGE_RECEIVED listeners.')
        for listener in self.event_listeners["MESSAGE_RECEIVED"]:
            logging.debug('Firing a listener...')
            listener(message)
