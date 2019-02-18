""" Main IRC bot module. """

from twisted.words.protocols import irc
#from twisted.internet import reactor, protocol

class IRCBot(irc.IRCClient):
  """ IRC bot class. These are produced at IRC bot factories. Do not attempt to craft by hand. """

  def __init__(self, nickname, ident, realname, channels):
    self.nickname = nickname
    self.ident = ident
    self.realname = realname
    self.channels = channels

  def connectionMade(self):
    super().connectionMade()
    print("Connected!")

  # def connectionLost(self, reason):
  #   super().connectionLost(reason)

  #event callbacks
  def signedOn(self):
    for channel in self.channels:
      self.join(channel)
