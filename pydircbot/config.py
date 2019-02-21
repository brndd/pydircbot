""" here be configs """

import os
import sys
from ruamel.yaml import YAML

class ConfigManager():
  """ I manage all the configuration. """
  #for now this class is very sparse. I expect it might be more complicated in the future.

  def __init__(self, filename="config.yaml"):
    """ opens a configuration file and loads its contents into this object """
    #TODO: sanity check the config file
    filepath = os.path.join(get_location(), filename)
    if not os.path.exists(filepath):
      create_default_config(filename)
    with open(filepath, "r") as cfgfile:
      yaml = YAML()
      self.config = yaml.load(cfgfile)

  # def get_config_value(self, configstring: "eg. irc.servers.freenode.host"):
  #   """
  #     returns a config value matching the given string, or None if no matches are found.
  #   """
  #   raise NotImplementedError


def create_default_config(filename="config.yaml", force=False):
  """
      Creates a default configuration file, should it be missing
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
            "quitmessage": "Bye.",
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
          },
          "discord": {
            "token": "put your token here"
          }
        }
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(cfg, cfgfile)
    except IOError as error:
      sys.exit(error)

def get_location():
  """
      retuns the full file path used to run the bot
  """
  return sys.path[0]
