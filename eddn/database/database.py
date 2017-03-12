from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, text
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

  def insertMessage(self, json):
    db_msg = Message(message_raw=json, message=json)
    session = self.Session()
    session.add(db_msg)
    session.commit()
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
###########################################################################
