import logging

from pydircbot.bot import PyDIRCBot
from pydircbot.config import ConfigManager


def main():
    logging.basicConfig(level=logging.DEBUG)
    config = ConfigManager()
    bot = PyDIRCBot(config)
    bot.start()


if __name__ == '__main__':
    main()
