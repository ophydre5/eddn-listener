from sqlalchemy import create_engine, desc, exc, event, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Text, text, Boolean
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql.json import JSON, JSONB

###########################################################################
# Our base class for database operations
###########################################################################
class database(object):
  def __init__(self, url, __logger):
    db_engine = create_engine(url)
    Base.metadata.create_all(db_engine)
    self.Session = sessionmaker(bind=db_engine)
    self.__logger = __logger

  def insertMessage(self, json, schemaref, gatewaytimestamp, blacklisted, message_valid, schema_test):
    __attempts = 0
    __max_attempts = 3
    __attempt_sleep = 5
    while __attempts < __max_attempts:
      try:  
        db_msg = Message(
          message_raw = json,
          message = json,
          blacklisted = blacklisted,
          message_valid = message_valid,
          schema_test = schema_test,
          schemaref = schemaref,
          gatewaytimestamp = gatewaytimestamp
        )
        session = self.Session()
        session.add(db_msg)
        session.commit()
        break
      except sqlalchemy.exc.OperationalError as ex:
        self.__logger.error("database.insertMessage(): Database OperationalError - Sleeping " + __attempt_sleep + " seconds then trying again...")
        __attempts += 1
        os.sleep(__attempt_sleep)
      except:
        raise
    if __attempts == __max_attempts:
      self.__logger.error("database.insertMessage(): Reached __max_attempts (" + __max_attempts + ") - message dropped")

  def latestMessageTimestamp(self, archiveType):
    session = self.Session()
    results = session.query(Message.message).filter(Message.schemaref == archiveType).order_by(desc(Message.gatewaytimestamp)).limit(1)
    for r in results:
      return r.message['header']['gatewayTimestamp']
###########################################################################

###########################################################################
# sqlalchemy definitions
###########################################################################
Base = declarative_base()

class Message(Base):
  __tablename__ = "messages"

  id = Column(Integer, autoincrement=True, primary_key=True)
  received = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"), index=True)
  message_raw = Column(JSON)
  message = Column(JSONB)
  blacklisted = Column(Boolean)
  message_valid = Column(Boolean)
  schema_test = Column(Boolean)
  schemaref = Column(Text, index=True)
  gatewaytimestamp = Column(TIMESTAMP, nullable=False, index=True)
###########################################################################
