"""
  Main Discord bot module. It's called disc.py so as to not conflict with discord.py the library.
"""

import logging
import asyncio

import discord

import pydircbot.adapters as adapters

class DiscordBot(discord.Client):
  """ The main Discord bot class. """

  def __init__(self, *args, **kwargs):
    self._adapter = kwargs.pop('adapter')
    super().__init__(*args, **kwargs)

  def run(self, *args, **kwargs):
    """ Runs the bot in a very simple way. Run this in a separate thread.
        You'll need to handle clean shutdown yourself (by calling stop()). """
    self.loop.run_until_complete(self.start(*args, **kwargs))

  def stop(self):
    """ Shuts the bot down cleanly (hopefully). """
    #we'll just use _do_cleanup for now even though it fucks the entire event loop
    self._do_cleanup()

  ########
  #Events#
  ########
  #these are coroutines so hopefully we can call blocking shit from them without borking everything
  #presumably the library is smart enough for this

  async def on_message(self, message):
    """ Executed when a message is received. """
    #this also gets executed for messages *we* send, which we probably don't care about
    if message.author == self.user:
      return
    simple_message = message.clean_content
    reply_handle = DiscordReplyHandle(self, message)
    coro = self._adapter.message_received(simple_message, reply_handle)
    asyncio.run_coroutine_threadsafe(coro, self._adapter.loop)

class DiscordReplyHandle(adapters.IReplyHandle):
  """ Pass me along to event listeners so they can reply if they want to. """

  def __init__(self, bot, source_message):
    self._bot = bot #reference to the bot itself
    self._source_message = source_message #the message that we're replying to

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
        self.reply(message, retry=retry-1)
      else:
        #if it fails again we'll just drop the issue
        logging.error('Failed to send Discord message. Reason: %s', ex.__class__.__name__)
    except discord.InvalidArgument:
      #this is only raised in case there are invalid attachments... which we don't use, but whatever
      logging.error('Invalid attachments for Discord message.')

  def reply_with_highlight(self, message):
    mention = self._source_message.author.mention
    self.reply(mention + ' ' + message)
