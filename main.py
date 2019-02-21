import logging

from pydircbot.bot import PyDIRCBot
from pydircbot.config import ConfigManager


def main():
    logging.basicConfig(level=logging.DEBUG)
    config = ConfigManager()
    bot = PyDIRCBot(config)

    def test_bridge(message):
        from pydircbot.disc import DiscordMessage
        import asyncio

        bridges = config.config['channel_mapping']
        dest = None
        if isinstance(message, DiscordMessage):
            source = message.source.id
            for bridge in bridges:
                if bridge['discord_channel'] == source:
                    dest = (bridge['irc_network'], bridge['irc_channel'])
                    break
        else:
            source = message.source
            for bridge in bridges:
                if (bridge['irc_network'], bridge['irc_channel']) == source:
                    dest = bridge['discord_channel']
                    break
        named_message = f"<{str(message.simple_sender)}> {message}"
        coro = bot.send_message(dest, str(named_message))
        asyncio.create_task(coro)

    bot.register_event("MESSAGE_RECEIVED", test_bridge)
    bot.start()


if __name__ == '__main__':
    main()
