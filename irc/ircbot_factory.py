""" Provides the factory class for IRC bots. """

from twisted.internet import protocol
from irc.ircbot import IRCBot

class IRCBotFactory(protocol.ClientFactory):
  """ The factory class for IRC bots. """
  def __init__(self, channel):
    self.channel = channel

  def buildProtocol(self, addr):
    bot = IRCBot(self.channel)
    
    return bot
