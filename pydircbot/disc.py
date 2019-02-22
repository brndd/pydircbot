"""
  Main Discord bot module. It's called disc.py so as to not conflict with discord.py the library.
"""

import logging
import asyncio

import discord

from . import adapters


class DiscordBot(discord.Client):
    """ The main Discord bot class. """

    def __init__(self, *args, **kwargs):
        self._adapter = kwargs.pop('adapter')
        self.webhooks_by_channel = {}
        self.webhooks_by_id = {}
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        """ Runs the bot in a very simple way. Run this in a separate thread.
        You'll need to handle clean shutdown yourself (by calling stop()). """
        self.loop.run_until_complete(self.start(*args, **kwargs))

    def stop(self):
        """ Shuts the bot down cleanly (hopefully). """
        #we'll just use _do_cleanup for now even though it fucks the entire event loop
        self._do_cleanup()

    def add_webhook(self, webhook_url, channel):
        """
        Adds a webhook that's attached to the given channel. These can be used for relaying messages to these channels.
        """
        #pylint:disable=protected-access
        adapter = discord.AsyncWebhookAdapter(session=self.http._session)
        webhook = discord.Webhook.from_url(webhook_url, adapter=adapter)
        self.webhooks_by_channel[channel] = webhook
        self.webhooks_by_id[webhook.id] = webhook

    async def relay_via_webhook(self, channel_id, message):
        """
        Relays the given message to the target channel through a webhook. The webhook will be taken from the dict.
        If no webhook is found, a ValueError is raised.
        channel_id is the integer id of the channel, message is an IMessage object.
        """
        webhook = self.webhooks_by_channel.get(channel_id)
        if webhook is None:
            raise ValueError("The given channel has no known webhook.")
        #check if there's a user with the same nickname on our server, and if there is, use their avatar
        channel = self.get_channel(channel_id)
        avatar_url = None
        if isinstance(channel, discord.TextChannel):
            member = discord.utils.find(lambda m: m.name == message.simple_sender, channel.guild.members)
            if member is not None:
                avatar_url = member.avatar_url
        await webhook.send(str(message), username=message.simple_sender, avatar_url=avatar_url)

    ########
    #Events#
    ########

    async def on_message(self, message):
        """ Executed when a message is received. """
        #this also gets executed for messages *we* send, which we don't want
        if message.author == self.user:
            return
        #it also gets executed for webhook messages that we might have sent, so ignore all webhook messages
        #from the webhooks that we use
        if message.webhook_id in self.webhooks_by_id:
            return
        discordmessage = DiscordMessage(self, message)
        coro = self._adapter.message_received(discordmessage)
        asyncio.run_coroutine_threadsafe(coro, self._adapter.loop)


class DiscordMessage(adapters.IMessage):
    """ Pass me along to event handlers as the message. """

    def __init__(self, bot, source_message):
        self._bot = bot
        self._source_message = source_message

    #pylint:disable=arguments-differ
    def reply(self, message, retry=1):
        channel = self._source_message.channel
        try:
            coro = channel.send(content=message)
            asyncio.run_coroutine_threadsafe(coro, self._bot.loop)
        except discord.HTTPException as ex:
            #if sending fails we'll try again until we're out of retries
            if retry > 0:
                logging.warning('Failed to send Discord message, retrying...')
                self.reply(message, retry=retry - 1)
            else:
                #if it fails again we'll just drop the issue
                logging.error('Failed to send Discord message. Reason: %s', ex.__class__.__name__)
        except discord.InvalidArgument:
            #this is only raised in case there are invalid attachments... which we don't use, but whatever
            logging.error('Invalid attachments for Discord message.')

    def reply_with_highlight(self, message):
        mention = self._source_message.author.mention
        self.reply(mention + ' ' + message)

    @property
    def protocol(self):
        return self.Protocol.DISCORD

    @property
    def source(self):
        return self._source_message.channel

    @property
    def sender(self):
        return self._source_message.author

    @property
    def simple_sender(self):
        return self._source_message.author.display_name

    @property
    def message(self):
        message_content = self._source_message.clean_content
        #append attachment URLs to the string representation of the message
        for attachment in self._source_message.attachments:
            if message_content == "":  #petty beautifying
                message_content += f'{attachment.url}'
            else:
                message_content += f' {attachment.url}'
        return message_content

    def __str__(self):
        return self.message
