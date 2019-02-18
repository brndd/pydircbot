from twisted.internet import reactor

from irc.ircbot_factory import IRCBotFactory
import config.config as config

def main():
  # a = IRCBotFactory("#dircbottest")
  # reactor.connectTCP("irc.freenode.net", 6667, a)
  # b = IRCBotFactory("#dircbottest")
  # reactor.connectTCP("irc.quakenet.org", 6667, b)
  # reactor.run()
  config.create_default_config()


if __name__ == '__main__':
  main()
