""" A wrapper to contain and control IRC bots. """
from twisted.internet import reactor

from irc.ircbot_factory import IRCBotFactory
from misc.singleton import Singleton


class IRCBotController(metaclass=Singleton):
  """ This class contains and controls our IRC bot instances """

  def add_bot(self):
    """ adds a new bot to this controller """
    pass
