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

  def insertMessage(self, json, blacklisted, message_valid, schema_test):
    try:  
      db_msg = Message(
        message_raw = json,
        message = json,
        blacklisted = blacklisted,
        message_valid = message_valid,
        schema_test = schema_test
      )
      session = self.Session()
      session.add(db_msg)
      session.commit()
    except:
      raise

  def latestMessageTimestamp(self):
    session = self.Session()
    for r in session.query(Message.message).order_by(Message.id.desc()).limit(1):
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
###########################################################################
