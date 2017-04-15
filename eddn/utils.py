import eddn.message
from eddn.message.message import JSONParseError, JSONValidationFailed, SoftwareBlacklisted

def validateEDDNMessage(msg, config, logger):
  try:
    #print(msg)
    __eddn_message = eddn.message(msg, config, logger)
  except JSONParseError as Ex:
    __json, __message = Ex.args
    logger.warning(__message)
    return (None, None, None, None)
  except TypeError as Ex:
    logger.error("Type Error\n%s", msg)
    raise

  __message_valid = True
  __message_blacklisted = False
  try:
    __eddn_message.validate()
  except JSONValidationFailed as Ex:
    logger.warning(Ex.args)
    __message_valid = False
    __message_blacklisted = None
  except SoftwareBlacklisted as Ex:
    name, version = Ex.args
    logger.info("Blacklisted " + name + " (" + version + ")")
    __message_blacklisted = True
  __message_schema_is_test = __eddn_message.schema_is_test
  return (__eddn_message, __message_valid, __message_blacklisted, __message_schema_is_test)
