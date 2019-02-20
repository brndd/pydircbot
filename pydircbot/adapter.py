""" Provides adapters for the underlying libraries. """

class IReplyHandle():
  """ Event listeners get passed a handle that they can use to easily reply to the message that
      fired the event. This is an interface for such handles; the implementation will
      vary by protocol. """

  def reply(self, message):
    """ Sends the given message as a reply. The message may be a string or whatever type
        is necessary for the protocol (but a string must always work). """
    raise NotImplementedError

  def reply_with_highlight(self, message):
    """ Sends the given message as a reply, with a highlight of the user we're replying to
        (by eg. prepending the user's nick followed by colon followed by space before the message,
        if we're on IRC). The message may be a string or whatever type is necessary for the
        protocol (but a string must always work). """
    raise NotImplementedError
