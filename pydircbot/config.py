""" here be configs """

import os
import sys
import yaml

from pydircbot.misc import Singleton

class ConfigManager(metaclass=Singleton):
  """ I manage all the configuration. """

  def __init__(self, filename="config.yaml"):
    """ opens a configuration file and loads its contents into this object """
    filepath = os.path.join(get_location(), filename)
    if not os.path.exists(filepath):
      create_default_config(filename)
    with open(filepath, "r") as cfgfile:
      self._config = yaml.load(cfgfile)

  def get_config_value(self, configstring):
    """
      returns a config value matching the given string, or None if no matches are found.
      @param configstring config string such as "irc.servers.freenode.host"
    """
    raise NotImplementedError


def create_default_config(filename="config.yaml", force=False):
  """
      Creates a default configuration file, should it be missing
      @param filename the name of the config file, default "config.yaml"
      @param force overwrite existing file?
  """
  filepath = os.path.join(get_location(), filename)
  if not os.path.exists(filepath) or force:
    try:
      with open(filepath, "w") as cfgfile:
        cfg = {
          "irc": {
            "nick": "pydircbot",
            "ident": "pydircbot",
            "realname": "pydircbot",
            "servers": {
              "freenode": {
                "host": "irc.freenode.net",
                "port": 6667,
                "channels": ["#pydircbot", "#pydircbot2"]
              },
              "quakenet": {
                "host": "irc.quakenet.org",
                "port": 6667,
                "channels": ["#pydircbot"]
              }
            }
          }
        }
        yaml.dump(cfg, cfgfile)
    except IOError as error:
      sys.exit(error)

def get_location():
  """
      retuns the full file path used to run the bot
  """
  return sys.path[0]
