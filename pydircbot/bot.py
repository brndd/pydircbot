""" The main module of the bot. """

from threading import Thread
import logging

from twisted.internet import reactor

import pydircbot.irc as irc
import pydircbot.disc as disc

class PyDIRCBot():
  """ The main bot class. """

  def __init__(self, config):
    """ Creates a new bot from the given config object. """
    self.config = config

    #Handle IRC part of config
    self._twisted_thread = None #this will contain a handle to the reactor.run() thread later
    icfg = config.config['irc']
    self.ircbots = {} #this stores bot factories rather than bots themselves
    bot_info = irc.IRCBotInfo(nickname=icfg['nick'], ident=icfg['ident'], realname=icfg['realname'])
    for server, server_info in icfg['servers'].items():
      factory = irc.IRCBotFactory(bot_info, server_info['channels'], server, self)
      self.ircbots[server] = factory
      #the bots won't *actually* connect until reactor.run()
      reactor.connectTCP(server_info['host'], server_info['port'], factory)

    #Handle Discord part of config
    self._discord_thread = None
    self.discordbot = disc.DiscordBot(adapter=self)

  def start(self):
    """ Connects all the bots. In practice this means running Twisted's reactor
        and whatever discord.py wants. """
    #reactor.run() is blocking so we run it in a separate thread
    #if we want the reactor to do something we must use thread-safe methods
    #such as reactor.callFromThread()
    self._twisted_thread = Thread(target=reactor.run, name="twistedreactor",
                                  kwargs={'installSignalHandlers': False})
    self._twisted_thread.start()

    #TODO: we'll just put this in another thread for the time being, but this is probably not the
    #best way of doing it
    token = self.config.config['discord']['token']
    self._discord_thread = Thread(target=self.discordbot.run_shittily, name="discordbot", args=(token,))
    self._discord_thread.start()

  def stop(self):
    """ Cleanly stops all the bots. """
    reactor.stop()
    #TODO: stop the discord bot cleanly

  ########
  #Events#
  ########

  #Supported event types that can be registered for
  event_listeners = {
    "MESSAGE_RECEIVED": set()
  }

  def register_event(self, event_type, listener):
    """ Registers an event listener to listen to an event. """
    if event_type not in self.event_listeners:
      raise ValueError("Invalid event type.")
    self.event_listeners[event_type].add(listener)

  def unregister_event(self, event_type, listener):
    """ Unregisters an event listener from the given event. """
    if event_type not in self.event_listeners:
      raise ValueError("Invalid event type.")
    self.event_listeners[event_type].discard(listener)

  #actual event callers
  def message_received(self, message, reply_handle):
    """ Called when a message is received.
        Fires all event listeners listening to the MESSAGE_RECEIVED event. """
    for listener in self.event_listeners["MESSAGE_RECEIVED"]:
      listener(message, reply_handle)
