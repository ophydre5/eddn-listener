#!/usr/bin/env python3
#
#
#

import sys, os
import time
import logging
import argparse
import json

import zlib
import zmq

import eddn
from eddn.message.message import JSONParseError, JSONValidationFailed, SoftwareBlacklisted
from eddn.utils import validateEDDNMessage

import threading

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
__configfile_fd = os.open("eddnlistener-config.json", os.O_RDONLY)
__configfile = os.fdopen(__configfile_fd)
__config = json.load(__configfile)
###########################################################################

"""
 "  Start
"""

###########################################################################
# Logging
###########################################################################
os.environ['TZ'] = 'UTC'
__default_loglevel = logging.INFO
__logger = logging.getLogger('eddnlistener')
__logger.setLevel(__default_loglevel)
__logger_ch = logging.StreamHandler()
__logger_ch.setLevel(__default_loglevel)
__logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s: %(message)s')
__logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S';
__logger_formatter.default_msec_format = '%s.%03d'
__logger_ch.setFormatter(__logger_formatter)
__logger.addHandler(__logger_ch)
###########################################################################

###########################################################################
# Command-Line Arguments
###########################################################################
__parser = argparse.ArgumentParser()
__parser.add_argument("--loglevel", help="set the log level to one of: DEBUG, INFO (default), WARNING, ERROR, CRITICAL")
__args = __parser.parse_args()
if __args.loglevel:
  __level = getattr(logging, __args.loglevel.upper())
  __logger.setLevel(__level)
  __logger_ch.setLevel(__level)
###########################################################################

##############################################################################
def main():
  __logger.info('Initialising Database Connection')
  __db = eddn.database(__config['database']['url'])

  
  __context   = zmq.Context()
  __subscriber  = __context.socket(zmq.SUB)
  
  __subscriber.setsockopt(zmq.SUBSCRIBE, b"")
  __subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)


  __logger.info('Starting EDDN Subscriber')
  ############################################################################
  while True:
    __first = True
    ##########################################################################
    try:
      __subscriber.connect(__relayEDDN)
      __logger.info('Connect to ' + __relayEDDN)
      
      ########################################################################
      while True:
        __message   = __subscriber.recv()
        
        if __message == False:
          __subscriber.disconnect(__relayEDDN)
          __logger.warning('Disconnect from ' + __relayEDDN)
          break
        
        __logger.debug('Got a message')

        __message   = zlib.decompress(__message)
        if __message == False:
          __logger.warning('Failed to decompress message')
          continue

        ###############################################################
        # Validate message against relevant schema and blacklist
        ###############################################################
        (__eddn_message, __message_valid, __message_blacklisted, __message_schema_is_test) = validateEDDNMessage(__message, __config, __logger)
        if not __eddn_message:
          continue

        ###############################################################
        # Insert data into database
        ###############################################################
        # If this is the first message fill in any gap from eddn-archive
        if __first:
          __eddnarchive_thread = threading.Thread(target=eddnarchiveThread, args=(__db,__eddn_message.json['header']['gatewayTimestamp']))
          __threads = []
          __threads.append(__eddnarchive_thread)
          __eddnarchive_thread.start()
          time.sleep(5)
          # For testing when we want only the separate thread running
          #__eddnarchive_thread.join()
          #exit(0)
          __first = False

        __db.insertMessage(__eddn_message.json, __message_blacklisted, __message_valid, __message_schema_is_test)
        ###############################################################
      ########################################################################

    except zmq.ZMQError as e:
      __logger.error('ZMQSocketException: ' + str(e))
      __subscriber.disconnect(__relayEDDN)
      __logger.warning('Disconnect from ' + __relayEDDN)
      time.sleep(5)
    ##########################################################################
  ############################################################################
##############################################################################

##############################################################################
def eddnarchiveThread(__db, __endgatewayTimestamp):
  __logger.info("First message, checking eddn-archive...")
  __archive = eddn.archive(__config, __logger, __db)

  ############################################################################
  for a in __config['eddnarchive']['archivetypes']:
    for v in a.values():
      __latestMessageTimestamp = __db.latestMessageTimestamp(v)
      if not __latestMessageTimestamp:
        continue
      __logger.debug("For '%s' __latestMessageTimestamp = %s", a, __latestMessageTimestamp)
      for k in a.keys():
        __logger.info("Current latest gatewayTimestamp for %s is %s", k, __latestMessageTimestamp)
        __archive.getTimeRange(k, __latestMessageTimestamp, __endgatewayTimestamp)
  ############################################################################

  __logger.info("Backfill from EDDN Archive finished")
##############################################################################

if __name__ == '__main__':
  main()
