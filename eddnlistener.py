#!/usr/bin/env python3
#
#
#

import sys, os
import logging
import argparse
import json

import zlib
import zmq

from distutils.version import LooseVersion

import simplejson
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

###########################################################################
# Configuration
###########################################################################
configfile_fd = os.open("eddnlistener-config.json", os.O_RDONLY)
configfile = os.fdopen(configfile_fd)
__config = json.load(configfile)
###########################################################################

"""
 "  Start
"""

###########################################################################
# Setup SQLAlchemy-related classes/data
###########################################################################
Base = declarative_base()
class Message(Base):
  __tablename__ = 'messages'

  id = Column(Integer, autoincrement=True, primary_key=True)
  received = Column(TIMESTAMP, nullable=False, server_default=text('NOW()'), index=True)
  message_raw = Column(JSON)
  message = Column(JSONB)
###########################################################################

###########################################################################
# Logging
###########################################################################
os.environ['TZ'] = 'UTC'
__default_loglevel = logging.INFO
logger = logging.getLogger('eddnlistener')
logger.setLevel(__default_loglevel)
logger_ch = logging.StreamHandler()
logger_ch.setLevel(__default_loglevel)
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S';
logger_formatter.default_msec_format = '%s.%03d'
logger_ch.setFormatter(logger_formatter)
logger.addHandler(logger_ch)
###########################################################################

###########################################################################
# Command-Line Arguments
###########################################################################
parser = argparse.ArgumentParser()
parser.add_argument("--loglevel", help="set the log level to one of: DEBUG, INFO (default), WARNING, ERROR, CRITICAL")
args = parser.parse_args()
if args.loglevel:
  level = getattr(logging, args.loglevel.upper())
  logger.setLevel(level)
  logger_ch.setLevel(level)
###########################################################################

def main():
  logger.info('Initialising Database Connection')
  db_engine = create_engine(__config['database']['url'])
  Base.metadata.create_all(db_engine)
  Session = sessionmaker(bind=db_engine)

  logger.info('Starting EDDN Subscriber')
  
  context   = zmq.Context()
  subscriber  = context.socket(zmq.SUB)
  
  subscriber.setsockopt(zmq.SUBSCRIBE, b"")
  subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)

  while True:
    try:
      subscriber.connect(__relayEDDN)
      logger.info('Connect to ' + __relayEDDN)
      
      while True:
        __message   = subscriber.recv()
        
        if __message == False:
          subscriber.disconnect(__relayEDDN)
          logger.warning('Disconnect from ' + __relayEDDN)
          break
        
        logger.debug('Got a message')

        __message   = zlib.decompress(__message)
        if __message == False:
          logger.warning('Failed to decompress message')
          continue

        __json    = simplejson.loads(__message)
        if __json == False:
          logger.warning('Failed to parse message as json')
          continue
        #logger.info(__json)
        
        ###############################################################
        # Validate message against relevant schema
        ###############################################################
        if not '$schemaRef' in __json:
          logger.warning("Message doesn't have a $schemaRef")
          continue

        # Pull the schema part out
        __schema = re.match('^http:\/\/schemas\.elite-markets\.net\/eddn\/(?P<part>[^\/]+)\/[0-9]+', __json['$schemaRef'])
        if not __schema:
          logger.warning("$schemaRef did not match regex: " + __json['$schemaRef'])
          continue

        if not __schema.group('part'):
          logger.warning("Couldn't find 'part' in $schemaRef" + __json['$schemaRef'])
          continue

        __knownSchema = False
        for s in __config['schemas']:
          if __schema.group('part') == s.get('name'):
            __knownSchema = True
            schemainfo = s
            break
        if not __knownSchema:
          logger.warning("Unknown schema: " + __json['$schemaRef'])
          continue

        if not schemainfo['message_schema'] == __json['$schemaRef']:
          logger.warning("In-message %schemaRef (" + __json['$schemaRef'] + ") doesn't precisely match expected schemaRef (" + schemainfo['message_schema'] + ")")
          continue

        if not schemainfo.get('schema'):
          logger.debug("Schema '" + __schema.group('part') + "' not yet loaded, doing so...")
          filename = "schemas/" + schemainfo['local_schema']
          schema_fd = open(filename, 'rt')
          schema_str = schema_fd.read(None)
          schemainfo['schema'] = simplejson.loads(schema_str)
          schema_fd.close()
          #logger.debug("loaded schema: " + schemainfo['schema'])

        #logger.debug("validate on received json: " + str(__json))
        try:
          validate(__json, schemainfo['schema'])
          logger.debug("Message validates against schema.")
        except SchemaError as e:
          logger.warning("Schema for " + __schema.group('part') + " wasn't valid")
          continue
        except ValidationError as e:
          logger.warning("Message failed to validate against schema")
        ###############################################################

        ###############################################################
        # Check against blacklist
        ###############################################################
        blackListed = False
        logger.debug('Checking softwareName: ' + __json['header']['softwareName'])
        for b in __config['blacklist']:
          logger.debug('Checking softwareName against' + b.get('softwarename'))
          if __json['header']['softwareName'].lower() == b.get('softwarename').lower():
            logger.debug('Matching softwareName found, checking if we have version preference')
            if b.get('goodversion'):
              logger.debug('We have known good version of: ' + b.get('goodversion'))
              if LooseVersion(__json['header']['softwareVersion']) < LooseVersion(b.get('goodversion')):
                logger.debug(__json['header']['softwareVersion'] + ' < ' + b.get('goodversion'))
                blackListed = True
            else:
              blackListed = True

          if blackListed == True:
            logger.info("Blacklisted softwareName: " + __json['header']['softwareName'])
            break
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
      logger.error('ZMQSocketException: ' + str(e))
      subscriber.disconnect(__relayEDDN)
      logger.warning('Disconnect from ' + __relayEDDN)
      time.sleep(5)
      
    

if __name__ == '__main__':
  main()
