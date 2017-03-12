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

import eddn
from eddn.message.message import JSONParseError, JSONValidationFailed, SoftwareBlacklisted

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
  db = eddn.database(__config['database']['url'])

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

        try: 
          eddn_message = eddn.message(__message, __config, logger)
        except JSONParseError as Ex:
          __json, __message = Ex.args
          logger.warning(__message)
          continue
        
        ###############################################################
        # Validate message against relevant schema and blacklist
        ###############################################################
        __message_valid = True
        __message_blacklisted = False
        try:
          eddn_message.validate()
        except JSONValidationFailed as Ex:
          logger.warning(Ex.args)
          __message_valid = False
          __message_blacklisted = None
        except SoftwareBlacklisted as Ex:
          name, version = Ex.args
          logger.info("Blacklisted " + name + " (" + version + ")")
          __message_blacklisted = True

        ###############################################################
        # Insert data into database
        ###############################################################
        db.insertMessage(eddn_message.json, __message_blacklisted, __message_valid)
        ###############################################################

    except zmq.ZMQError as e:
      logger.error('ZMQSocketException: ' + str(e))
      subscriber.disconnect(__relayEDDN)
      logger.warning('Disconnect from ' + __relayEDDN)
      time.sleep(5)
      
    

if __name__ == '__main__':
  main()
