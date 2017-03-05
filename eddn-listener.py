#!/usr/bin/env python3
#
#
#

import zlib
import zmq
import simplejson
import sys, os, datetime, time
from jsonschema import validate
import re
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql.json import JSON, JSONB

"""
 "  Configuration
"""
__relayEDDN       = 'tcp://eddn-relay.elite-markets.net:9500'
__timeoutEDDN       = 600000

# Set False to listen to production stream
__debugEDDN       = False

# Set to False if you do not want verbose logging
__logVerboseFile    = os.path.dirname(__file__) + '/Logs_Verbose_EDDN_%DATE%.htm'
#__logVerboseFile    = False

###########################################################################
# Database
###########################################################################
__databaseURL       = 'postgresql://eddnlistener:6gQXLmMsA2guVjEGntYJe58V7VGT6MsL@localhost:5433/eddn';
###########################################################################

###########################################################################
# List of blacklisted softwares
###########################################################################
__blacklistedSoftwares   = [
  'ed-ibe (api)',
  'ed central production server',
  'eliteocr',
  'regulatednoise__dj',
  'ocellus - elite: dangerous assistant'
# and eddi <= 2.2
]
###########################################################################

###########################################################################
# Schemas we know about, so are interested in
###########################################################################
__knownSchemas = {
  "blackmarket":
    {
      "message_schema" : "http://schemas.elite-markets.net/eddn/blackmarket/1",
      "local_schema" : "blackmarket-01.json",
      "schema" : None
    }
  ,"commodity":
    {
      "message_schema" : "http://schemas.elite-markets.net/eddn/commodity/3",
      "local_schema" : "commodity-03.json",
      "schema" : None
    }
  ,"journal":
    {
      "message_schema" : "http://schemas.elite-markets.net/eddn/journal/1",
      "local_schema" : "journal-01.json",
      "schema" : None
    }
  ,"outfitting":
    {
      "message_schema" : "http://schemas.elite-markets.net/eddn/outfitting/2",
      "local_schema" : "outfitting-02.json",
      "schema" : None
    }
  ,"shipyard":
    {
      "message_schema" : "http://schemas.elite-markets.net/eddn/shipyard/2",
      "local_schema" : "shipyard-02.json",
      "schema" : None
    }
}
###########################################################################

"""
 "  Start
"""
def date(__format):
  d = datetime.datetime.utcnow()
  return d.strftime(__format)


__oldTime = False
def echoLog(__str):
  global __oldTime, __logVerboseFile
  
  if __logVerboseFile != False:
    __logVerboseFileParsed = __logVerboseFile.replace('%DATE%', str(date('%Y-%m-%d')))
  
  if __logVerboseFile != False and not os.path.exists(__logVerboseFileParsed):
    f = open(__logVerboseFileParsed, 'w')
    f.write('<style type="text/css">html { white-space: pre; font-family: Courier New,Courier,Lucida Sans Typewriter,Lucida Typewriter,monospace; }</style>')
    f.close()

  if (__oldTime == False) or (__oldTime != date('%H:%M:%S')):
    __oldTime = date('%H:%M:%S')
    __str = str(__oldTime)  + ' | ' + str(__str)
  else:
    __str = '    '  + ' | ' + str(__str)
    
  print (__str)
  sys.stdout.flush()

  if __logVerboseFile != False:
    f = open(__logVerboseFileParsed, 'a')
    f.write(__str + '\n')
    f.close()
  
Base = declarative_base()
class Message(Base):
  __tablename__ = 'messages'

  id = Column(Integer, autoincrement=True, primary_key=True)
  received = Column(TIMESTAMP, nullable=False, server_default=text('NOW()'), index=True)
  message_raw = Column(JSON)
  message = Column(JSONB)


def main():
  echoLog('Initialising Database Connection')
  db_engine = create_engine(__databaseURL);
  Base.metadata.create_all(db_engine)
  Session = sessionmaker(bind=db_engine)

  echoLog('Starting EDDN Subscriber')
  echoLog('')
  
  context   = zmq.Context()
  subscriber  = context.socket(zmq.SUB)
  
  subscriber.setsockopt(zmq.SUBSCRIBE, b"")
  subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)

  while True:
    try:
      subscriber.connect(__relayEDDN)
      echoLog('Connect to ' + __relayEDDN)
      echoLog('')
      echoLog('')
      
      while True:
        __message   = subscriber.recv()
        
        if __message == False:
          subscriber.disconnect(__relayEDDN)
          echoLog('Disconnect from ' + __relayEDDN)
          echoLog('')
          echoLog('')
          break
        
        echoLog('Got a message')

        __message   = zlib.decompress(__message)
        if __message == False:
          echoLog('Failed to decompress message')
          continue

        __json    = simplejson.loads(__message)
        if __json == False:
          echoLog('Failed to parse message as json')
          continue
        #echoLog(__json)
        
        ###############################################################
        # Validate message against relevant schema
        ###############################################################
        if not '$schemaRef' in __json:
          echoLog("Message doesn't have a $schemaRef")
          continue

        # Pull the schema part out
        __schema = re.match('^http:\/\/schemas\.elite-markets\.net\/eddn\/(?P<part>[^\/]+)\/[0-9]+', __json['$schemaRef'])
        if not __schema:
          echoLog("$schemaRef did not match regex: " + __json['$schemaRef'])
          continue

        if not __schema.group('part'):
          echoLog("Couldn't find 'part' in $schemaRef" + __json['$schemaRef'])
          continue

        if not __schema.group('part') in __knownSchemas:
          echoLog("Unknown schema: " + __json['$schemaRef'])
          continue

        schemainfo = __knownSchemas[__schema.group('part')]
        if not schemainfo['message_schema'] == __json['$schemaRef']:
          echoLog("In-message %schemaRef (" + __json['$schemaRef'] + ") doesn't precisely match expected schemaRef (" + schemainfo['message_schema'] + ")")
          continue

        if not schemainfo['schema']:
          echoLog("Schema '" + __schema.group('part') + "' not yet loaded, doing so...")
          filename = "schemas/" + schemainfo['local_schema']
          schema_fd = open(filename, 'rt')
          schema_str = schema_fd.read(None)
          schemainfo['schema'] = simplejson.loads(schema_str)
          schema_fd.close()
          #echoLog("loaded schema: " + schemainfo['schema'])

        #echoLog("validate on received json: " + str(__json))
        try:
          validate(__json, schemainfo['schema'])
          echoLog("Message validates against schema.")
        except SchemaError as e:
          echoLog("Schema for " + __schema.group('part') + " wasn't valid")
          continue
        except ValidationError as e:
          echoLog("Message failed to validate against schema")
        ###############################################################

        ###############################################################
        # Check against blacklist
        ###############################################################
        blackListed = False
        if __json['header']['softwareName'] in __blacklistedSoftwares:
          blackListed = True
          echoLog("Blacklisted softwareName: " + __json['header']['softwareName'])
        ###############################################################

        ###############################################################
        # Insert data into database
        ###############################################################
        db_msg = Message(message_raw=__json, message=__json)
        session = Session()
        session.add(db_msg)
        session.commit()
        ###############################################################

    except zmq.ZMQError as e:
      echoLog('')
      echoLog('ZMQSocketException: ' + str(e))
      subscriber.disconnect(__relayEDDN)
      echoLog('Disconnect from ' + __relayEDDN)
      echoLog('')
      time.sleep(5)
      
    

if __name__ == '__main__':
  main()
