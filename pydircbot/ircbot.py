""" Main IRC bot module. """

import logging
from twisted.words.protocols import irc
from twisted.internet import protocol

#Disable pylint warning for unimplemented methods because Twisted has decided to keep some funny
#forever unimplemented placeholder methods.
#pylint: disable=W0223
class IRCBot(irc.IRCClient):
  """ IRC bot class. These are produced at IRC bot factories. Do not attempt to craft by hand. """

  def __init__(self, nickname, ident, realname, channels, network):
    self.nickname = nickname
    self.ident = ident
    self.realname = realname
    self.channels = channels
    self.network = network

  def connectionMade(self):
    logging.info("Connection made to %s.", self.network)
    super().connectionMade()

  #event callbacks
  def signedOn(self):
    for channel in self.channels:
      self.join(channel)


class IRCBotFactory(protocol.ReconnectingClientFactory):
  """ The factory class for IRC bots. """

  def __init__(self, nickname, ident, realname, channels: "List of channels",
               network: "Name of the network as it appears in the config"):
    self.nickname = nickname
    self.ident = ident
    self.realname = realname
    self.channels = channels
    self.network = network

  def buildProtocol(self, addr):
    bot = IRCBot(self.nickname, self.ident, self.realname, self.channels, self.network)
    self.resetDelay()
    return bot

  def startedConnecting(self, connector):
    logging.info("Started connecting to %s.", self.network)
    super().startedConnecting(connector)

  def clientConnectionFailed(self, connector, reason):
    logging.error("Connection to %s failed. Reason: %s", self.network, reason)
    super().clientConnectionFailed(connector, reason)

  def clientConnectionLost(self, connector, reason):
    logging.error("Connection to %s lost. Reason: %s", self.network, reason)
    super().clientConnectionLost(connector, reason)
