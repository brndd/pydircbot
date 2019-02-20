""" Main IRC bot module. """

import logging
from collections import namedtuple

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor

import pydircbot.adapter as adapter

#a namedtuple used to pass around common info about bots
IRCBotInfo = namedtuple('IRCBotInfo', ['nickname', 'ident', 'realname'])

#Disable pylint warning for unimplemented methods because Twisted has decided to keep some funny
#forever unimplemented placeholder methods.
#pylint: disable=W0223
class IRCBot(irc.IRCClient):
  """ IRC bot class. These are produced at IRC bot factories. Do not attempt to craft by hand. """

  def __init__(self, bot_info, channels, network_name, adapter):
    self.nickname = bot_info.nickname
    self.ident = bot_info.ident
    self.realname = bot_info.realname
    self.channels = channels
    self.network_name = network_name
    self._adapter = adapter

  def connectionMade(self):
    logging.info("Connection made to %s.", self.network_name)
    super().connectionMade()

  def signedOn(self):
    for channel in self.channels:
      self.join(channel)

  def privmsg(self, user, channel, message):
    #call the adapter's event thing in a new thread
    reply_handle = IRCReplyHandle(self, user, channel)
    reactor.callInThread(self._adapter.message_received, message, reply_handle)


class IRCBotFactory(protocol.ReconnectingClientFactory):
  """ The factory class for IRC bots. """

  def __init__(self, bot_info: IRCBotInfo, channels: "List of channels", network_name, adapter):
    """ Creates a new factory for the given network. """
    self.bot_info = bot_info
    self.channels = channels
    self.network_name = network_name
    self._adapter = adapter
    self._bot = None

  def buildProtocol(self, addr):
    self._bot = IRCBot(self.bot_info, self.channels, self.network_name, self._adapter)
    self.resetDelay() #resets the reconnection delay
    return self._bot

  @property
  def bot(self):
    """ Returns the last IRCBot this factory built. """
    return self._bot

  def startedConnecting(self, connector):
    logging.info("Started connecting to %s.", self.network_name)
    super().startedConnecting(connector)

  def clientConnectionFailed(self, connector, reason):
    logging.error("Connection to %s failed. Reason: %s", self.network_name, reason)
    super().clientConnectionFailed(connector, reason)

  def clientConnectionLost(self, connector, reason):
    logging.error("Connection to %s lost. Reason: %s", self.network_name, reason)
    super().clientConnectionLost(connector, reason)


class IRCReplyHandle(adapter.IReplyHandle):
  """ Pass me along to event listeners so they can reply if they want to. """

  def __init__(self, bot, user, channel):
    self._bot = bot
    self.user = user #this seems to be nick!user@host
    self.nick = user.split('!', 1)[0]
    self.channel = channel

  def reply(self, message):
    #if this is a private message
    if self.channel == self._bot.nickname:
      reactor.callFromThread(self._bot.msg, self.nick, message)
    #otherwise send in the channel
    else:
      reactor.callFromThread(self._bot.msg, self.channel, message)

  def reply_with_highlight(self, message):
    self.reply(self.nick + ': ' + message)
