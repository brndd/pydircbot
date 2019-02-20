import logging

from pydircbot.bot import PyDIRCBot
from pydircbot.config import ConfigManager

def main():
  logging.basicConfig(level=logging.DEBUG)
  config = ConfigManager()
  bot = PyDIRCBot(config)
  bot.start()
  bot.register_event("MESSAGE_RECEIVED", lambda msg, handle: handle.reply_with_highlight(msg))

if __name__ == '__main__':
  main()
