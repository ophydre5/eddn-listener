import simplejson
import re
from jsonschema import validate, SchemaError
from distutils.version import LooseVersion

class message:
  """
  Class that handles parsing of a message as JSON and then validating it.
  """
  def __init__(self, message, config, logger):
    """
    Accepts the raw text of a JSON message, a config object and a logger
    object.

    Will raise a JSONParseError exception if the message can't be parsed as
    JSON.
    """
    self.config = config
    self.logger = logger
    try: 
      self.json = simplejson.loads(message)
      if not self.json:
        raise JSONParseError(message, "Failed to parse message as json")
    except Exception as ex:
      #print(type(ex))
      #print(ex.args)
      raise

  def validate(self):
    """
    Validates a message against relevant schema, and checks if the software
    name/version are on the blacklist.

    Sets member schema_is_test = True if a test schema is detected.

    Raises JSONValidationFailed with a reason (in string message) if the
    message doesn't validate for any reason.
    Raises SoftwareBlacklisted if the software Name, or version, is on the blacklist.
    """
    if not "$schemaRef" in self.json:
      raise JSONValidationFailed("Message doesn't have a $schemaRef")

    __schema = re.match("^http:\/\/schemas\.elite-markets\.net\/eddn\/(?P<part>[^\/]+)\/[0-9]+", self.json["$schemaRef"])
    if not __schema:
      raise JSONValidationFailed("$schemaRef did not match regex: " + self.json["$schemaRef"])

    __knownSchema = False
    for s in self.config["schemas"]:
      if __schema.group("part") == s.get("name"):
        __knownSchema = True
        schemainfo = s
        break
    if not __knownSchema:
      raise JSONValidationFailed("Unknown schema: " + self.json["$schemaRef"])

    self.schema_is_test = False
    if re.match(schemainfo["message_schema"], self.json["$schemaRef"]):
      if re.search('[0-9]+/test$', self.json["$schemaRef"]):
        self.schema_is_test = True
    else:
      raise JSONValidationFailed("In-message $schemaRef (" + self.json["$schemaRef"] + ") doesn't match expected schemaRef (" + schemainfo["message_schema"] + ")")

    if not schemainfo.get("schema"):
      self.logger.debug("Schema '" + __schema.group("part") + "' not yet loaded, doing so...")
      filename = "schemas/" + schemainfo["local_schema"]
      schema_fd = open(filename, "rt")
      schema_str = schema_fd.read(None)
      schema_fd.close()
      schemainfo["schema"] = simplejson.loads(schema_str)
      #self.logger.debug("loaded schema: " + schemainfo["schema"])

    try:
      validate(self.json, schemainfo["schema"])
      self.logger.debug("Message validates against schema.")
    except SchemaError as Ex:
      raise JSONValidationFailed("Message failed to validate against schema")

    try:
      __blackListed = False
      self.logger.debug("Checking softwareName: " + self.json["header"]["softwareName"])
      for b in self.config["blacklist"]:
        #self.logger.debug("Checking softwareName against" + b.get("softwarename"))
        if self.json["header"]["softwareName"].lower() == b.get("softwarename").lower():
          self.logger.debug("Matching softwareName '" + b.get("softwarename") + "' found, checking if we have version preference")
          if b.get("goodversion") and LooseVersion(self.json["header"]["softwareVersion"]) < LooseVersion(b.get("goodversion")):
            self.logger.debug("Blacklisted as " + self.json["header"]["softwareVersion"] + " < " + b.get("goodversion"))
            __blackListed = True
          else:
            self.logger.debug("Blacklisted ALL versions")
            __blackListed = True

      if __blackListed == True:
        raise SoftwareBlacklisted(self.json["header"]["softwareName"], self.json["header"]["softwareVersion"])
    except:
      raise

class Error(Exception):
  pass

class JSONParseError(Error):
  """
  Exception raised when a message couldn't be parsed as JSON.
  """
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class JSONValidationFailed(Error):
  def __init__(self, message):
    self.message = message

class SoftwareBlacklisted(Error):
  def __init__(self, softwareName, softwareVersion):
    self.softwareName = softwareName
    self.softwareVersion = softwareVersion

