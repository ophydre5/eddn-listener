from eddn.message.message import message, JSONParseError, JSONValidationFailed, SoftwareBlacklisted
import simplejson
from jsonschema import validate, ValidationError

import unittest
import os
import json
import logging

class EddnMessageTests(unittest.TestCase):
  ############################################################
  def setUp(self):
    try:
      configfile_fd = os.open("test_eddnlistener-config.json", os.O_RDONLY)
    except (FileNotFoundError):
      self.skipTest("No schemas config due to test_eddnlistener-config.json not found") 

    configfile = os.fdopen(configfile_fd)
    self.config = json.load(configfile)
    configfile.close()

    os.environ['TZ'] = 'UTC'
    __default_loglevel = logging.INFO
    self.logger = logging.getLogger('eddnlistener')
    self.logger.setLevel(__default_loglevel)
    logger_ch = logging.StreamHandler()
    logger_ch.setLevel(__default_loglevel)
    logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S';
    logger_formatter.default_msec_format = '%s.%03d'
    logger_ch.setFormatter(logger_formatter)
    self.logger.addHandler(logger_ch)
  ############################################################

  ############################################################
  # Invalid JSON
  ############################################################
  def test_invalidJSON(self):
    with self.assertRaises(simplejson.scanner.JSONDecodeError):
      m = message('{', self.config, self.logger)    
    with self.assertRaises(simplejson.scanner.JSONDecodeError):
      m = message('}', self.config, self.logger)    
  ############################################################

  ############################################################
  # No $schemaRef
  ############################################################
  def test_noSchemaRef(self):
    m = message(
      '{"message": {"event": "Docked"}}',
      self.config, self.logger)    
    with self.assertRaises(JSONValidationFailed):
      m.validate()
	############################################################

	############################################################
	# $schemaRef did not match regex
	############################################################
  def test_schemaRefNotMatched(self):
    m = message(
      '{"message": {"event": "Docked"}, "$schemaRef": "http://scXXXhemas.elite-markets.net/eddn/journal/1"}',
      self.config, self.logger)    
    with self.assertRaises(JSONValidationFailed):
      m.validate()
	############################################################

	############################################################
	# Unknown schema
	############################################################
  def test_unknownSchema(self):
    m = message(
      '{"message": {"event": "Docked"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/wibble/1"}',
      self.config, self.logger)    
    with self.assertRaises(JSONValidationFailed):
      m.validate()
	############################################################

	############################################################
	# In-Message $schemaRef doesn't match part-detected schemaRef
	############################################################
  def test_schemaNotMatchPartDetectedRegex(self):
    m = message(
      '{"message": {"event": "Docked"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/2"}',
      self.config, self.logger)    
    with self.assertRaises(JSONValidationFailed):
      m.validate()
	############################################################

	############################################################
	# schema_is_test
	############################################################
  def test_detectedSchemaIsTest(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Good Software", "softwareVersion": "2.2.6.2", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/1/test"}',
      self.config, self.logger)    
    m.validate()
    self.assertEqual(m.schema_is_test, True)
	############################################################

	############################################################
	#  In-message $schemaRef doesn't match expected schemaRef
	############################################################
  def test_schemaRefNotAsExpected(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Good Software", "softwareVersion": "2.2.6.2", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/2"}',
      self.config, self.logger)    
    with self.assertRaises(JSONValidationFailed):
      m.validate()
	############################################################

	############################################################
	# Schema fails to load - FileNotFoundError
	############################################################
  def test_schemaLoadFailsFileNotFoundError(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Good Software", "softwareVersion": "2.2.6.2", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/python_tests/1"}',
      self.config, self.logger)    
    with self.assertRaises(FileNotFoundError):
      m.validate()
	############################################################

	############################################################
	# Schema fails to load - FileNotFoundError
	############################################################
  def test_schemaLoadFailsJSONDecodeError(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Good Software", "softwareVersion": "2.2.6.2", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/python_tests_02/2"}',
      self.config, self.logger)    
    with self.assertRaises(simplejson.scanner.JSONDecodeError):
      m.validate()
	############################################################

	############################################################
	# foreach schema: Message validates against schema
	############################################################
  def test_messageValidatesAgainstSchema(self):
    # This is missing the mandatory message->timestamp element
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Good Software", "softwareVersion": "2.2.6.2", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/1"}',
      self.config, self.logger)    
    with self.assertRaises(ValidationError):
      m.validate()
	############################################################

	############################################################
	# Good softwareName NOT blacklisted
	############################################################
  def test_blacklistedGoodSoftwareNameAllowed(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Good SoftwareName", "softwareVersion": "0.6.1", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/1"}',
      self.config, self.logger)
    try:
      m.validate()
    except SoftwareBlacklisted:
      self.fail("'Test Good SoftwareName' raised SoftwareBlacklisted")
	############################################################

	############################################################
	# Blacklisted softwareName - all versions
	############################################################
  def test_blacklistedSoftwareNameDetected(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Bad SoftwareName", "softwareVersion": "0.6.1", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/1"}',
      self.config, self.logger)    
    with self.assertRaises(SoftwareBlacklisted):
      m.validate()
	############################################################

	############################################################
	# Blacklisted softwareName - only older than goodVersion
	############################################################
  def test_blacklistedSoftwareVersionDetected(self):
    m = message(
      '{"header": {"uploaderID": "Cmdr Jameson", "softwareName": "Test Bad SoftwareVersion", "softwareVersion": "13.0.1", "gatewayTimestamp": "2017-03-12T19:26:20.984504Z"}, "message": {"event": "Docked", "StarPos": [-21.531, -6.313, 116.031], "timestamp": "2017-03-12T19:26:20Z", "StarSystem": "Laksak", "StationName": "Littlewood Gateway", "StationType": "Orbis", "FactionState": "Expansion", "StationEconomy": "$economy_Agri;", "StationFaction": "Laksak Ltd", "StationAllegiance": "Federation", "StationGovernment": "$government_Corporate;"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/1"}',
      self.config, self.logger)    
    with self.assertRaises(SoftwareBlacklisted):
      m.validate()
    pass
	############################################################
###########################################################################
