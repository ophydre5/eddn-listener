from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, text, Boolean
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql.json import JSON, JSONB

###########################################################################
# Our base class for database operations
###########################################################################
class database(object):
  def __init__(self, url):
    db_engine = create_engine(url)
    Base.metadata.create_all(db_engine)
    self.Session = sessionmaker(bind=db_engine)

  def insertMessage(self, json, blacklisted, message_valid):
    try:  
      db_msg = Message(
        message_raw=json,
        message=json,
        blacklisted=blacklisted,
        message_valid = message_valid
      )
      session = self.Session()
      session.add(db_msg)
      session.commit()
    except:
      raise
###########################################################################

###########################################################################
# sqlalchemy definitions
###########################################################################
Base = declarative_base()

class Message(Base):
  __tablename__ = 'messages'

  id = Column(Integer, autoincrement=True, primary_key=True)
  received = Column(TIMESTAMP, nullable=False, server_default=text('NOW()'), index=True)
  message_raw = Column(JSON)
  message = Column(JSONB)
  blacklisted = Column(Boolean)
  message_valid = Column(Boolean)
###########################################################################

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
      self.db = database(__config['database']['url'])
    except OperationalError:
      self.skipTest("Failed to connect to database")

  def test_insertMessage_ValidJSON(self):
    try:
      self.db.insertMessage('{"header": {"uploaderID": "TenFourteen", "softwareName": "EDDI", "softwareVersion": "2.2.0", "gatewayTimestamp": "2017-03-12T14:09:18.786774Z"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/journal/1", "message": {"StarPos": [-5.375, 71.563, -54.25], "StarSystem": "Dietri", "SystemSecurity": "$SYSTEM_SECURITY_high;", "SystemFaction": "Dietri Limited", "timestamp": "2017-03-12T14:09:21Z", "SystemGovernment": "$government_Corporate;", "FactionState": "Boom", "event": "FSDJump", "SystemEconomy": "$economy_Agri;", "SystemAllegiance": "Federation"}}')
    except Exception as ex:
      print(type(ex))
      print(ex.args)
      raise
###########################################################################
