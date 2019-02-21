import logging
import threading

from pydircbot.bot import PyDIRCBot
from pydircbot.config import ConfigManager

def main():
  logging.basicConfig(level=logging.DEBUG)
  config = ConfigManager()
  bot = PyDIRCBot(config)
  def test_reply(msg, handle):
    handle.reply_with_highlight(msg)
  bot.register_event("MESSAGE_RECEIVED", test_reply)
  bot.start()

if __name__ == '__main__':
  main()
