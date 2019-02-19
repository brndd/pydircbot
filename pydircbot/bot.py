""" The main module of the bot that provides an adapter for the underlying libraries. """

from threading import Thread

from twisted.internet import reactor

import pydircbot.irc as irc

class PyDIRCBot():
  """ The main bot class. Provides an adapter for the underlying libraries,
      handling connections, events, etc. """

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

    #TODO: discord part

  def start(self):
    """ Connects all the bots. In practice this means running Twisted's reactor
        and whatever discord.py wants. """
    #reactor.run() is blocking so we run it in a separate thread
    #if we want the reactor to do something we must use thread-safe methods
    #such as reactor.callFromThread()
    self._twisted_thread = Thread(target=reactor.run, name="twistedreactor", kwargs={'installSignalHandlers': False})
    self._twisted_thread.start()

  def stop(self):
    """ Cleanly stops all the bots. """
    raise NotImplementedError #TODO: write this

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


class IReplyHandle():
  """ Event listeners get passed a handle that they can use to easily reply to the message that
      fired the event. This is an interface for such handles; the implementation will
      vary by protocol. """

  def reply(self, message):
    """ Sends the given message as a reply. The message may be a string or whatever type
        is necessary for the protocol (but a string must always work). """
    raise NotImplementedError

  def reply_with_highlight(self, message):
    """ Sends the given message as a reply, with a highlight of the user we're replying to
        (by eg. prepending the user's nick followed by colon followed by space before the message,
        if we're on IRC). The message may be a string or whatever type is necessary for the
        protocol (but a string must always work). """
    raise NotImplementedError


class IRCReplyHandle(IReplyHandle):
  """ Pass me along to event listeners so they can reply if they want to. """

  def __init__(self, bot, user, channel):
    self._bot = bot
    self.user = user #this seems to be nick!user@host
    self.channel = channel

  def reply(self, message):
    nick = self.user.split('!', 1)[0]
    #if this is a private message
    if self.channel == self._bot.nickname:
      reactor.callFromThread(self._bot.msg, nick, message)
    #otherwise send in the channel
    else:
      reactor.callFromThread(self._bot.msg, self.channel, message)
