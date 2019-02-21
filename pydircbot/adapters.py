""" Provides adapters for the underlying libraries. """


class IMessage():
    """
    A helper object to pass to event listeners to make their life easier.
    Facilitates checking where the message is from, easily replying to it, etc.
    """
    from enum import Enum

    class Protocol(Enum):
        """ This is used to identify the protocol the message is from. """
        IRC = 1
        DISCORD = 2

    def reply(self, message_text):
        """ Sends the given message as a reply. The message may be a string or whatever type
        is necessary for the protocol (but a string must always work). """
        raise NotImplementedError

    def reply_with_highlight(self, message_text):
        """ Sends the given message as a reply, with a highlight of the user we're replying to
        (by eg. prepending the user's nick followed by colon followed by space before the message,
        if we're on IRC). The message may be a string or whatever type is necessary for the
        protocol (but a string must always work). """
        raise NotImplementedError

    @property
    def protocol(self):
        """ Returns the protocol this message is from. """
        raise NotImplementedError

    @property
    def source(self):
        """ Returns the source (eg. channel) of this message in a format appropriate for the protocol. """
        raise NotImplementedError

    @property
    def sender(self):
        """ Returns the sender of this message in a format appropriate for the protocol. """
        raise NotImplementedError

    @property
    def simple_sender(self):
        """ Returns the sender in a simple no-frills form (eg. just their nickname and nothing else.) """
        raise NotImplementedError

    @property
    def message(self):
        """ This should return a printable string representation of the message's contents, stripped of any special
        control characters and such. """
        raise NotImplementedError

    def __str__(self):
        """ This should return a printable string representation of the message's contents, stripped of any special
        control characters and such. """
        raise NotImplementedError
