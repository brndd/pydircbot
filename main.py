from pydircbot.bot import PyDIRCBot
from pydircbot.config import ConfigManager

def main():
  config = ConfigManager()
  bot = PyDIRCBot(config)
  bot.start()
  bot.register_event("MESSAGE_RECEIVED", lambda msg, handle: handle.reply("You said: " + msg))

if __name__ == '__main__':
  main()
