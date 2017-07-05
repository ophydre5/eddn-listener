from eddn.database.database import database

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, text, Boolean
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql.json import JSON, JSONB

###########################################################################
# Tests
###########################################################################
import unittest
import os
import json
from sqlalchemy.exc import OperationalError

class EddnDatabaseTests(unittest.TestCase):
  def setUp(self):
    try:
      configfile_fd = os.open("eddnlistener-config.json", os.O_RDONLY)
    except (FileNotFoundError):
      self.skipTest("No Database config due to eddnlistener-config.json not found")

    configfile = os.fdopen(configfile_fd)
    __config = json.load(configfile)
    configfile.close()

    try:
      self.db = database(__config["database"]["url"])
    except OperationalError:
      self.skipTest("Failed to connect to database")

  def test_insertMessage_ValidJSON(self):
    try:
      self.db.insertMessage('{"header": {"uploaderID": "TenFourteen", "softwareName": "EDDI", "softwareVersion": "2.2.0", "gatewayTimestamp": "2017-03-12T14:09:18.786774Z"}, "$schemaRef": "https://eddn.edcd.io/schemas/journal/1", "message": {"StarPos": [-5.375, 71.563, -54.25], "StarSystem": "Dietri", "SystemSecurity": "$SYSTEM_SECURITY_high;", "SystemFaction": "Dietri Limited", "timestamp": "2017-03-12T14:09:21Z", "SystemGovernment": "$government_Corporate;", "FactionState": "Boom", "event": "FSDJump", "SystemEconomy": "$economy_Agri;", "SystemAllegiance": "Federation"}}', False, True, False)
    except Exception as ex:
      print(type(ex))
      print(ex.args)
      raise
###########################################################################
