import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout, TooManyRedirects
from time import sleep
from random import randint
import re
from datetime import datetime, timedelta
from eddn.message.message import JSONParseError, JSONValidationFailed, SoftwareBlacklisted
from eddn.utils import validateEDDNMessage

class archive:
  """
  Handles retrieving data from eddn-archive
  """

#############################################################################
  def __init__(self, config, logger, db):
    self.__config = config
    self.__logger = logger
    self.__db = db
#############################################################################

#############################################################################
  def getTimeRange(self, archive, start, end=None):
    self.__logger.debug("Starting")

    if not start:
      self.__logger.warn("No 'start', no data in database yet?")
      return []

    __startDateTime = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ")
    if end:
      self.__logger.debug("Using supplied end timestamp")
      __endDateTime = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
      self.__logger.debug("No end timestamp, using end of start day")
      __endOfDay = __startDateTime.strftime("%Y-%m-%dT23:59:59.999999Z")
      __endDateTime = datetime.strptime(__endOfDay, "%Y-%m-%dT%H:%M:%S.%fZ")

    self.__logger.debug("%s (%d) to %s (%d)", __startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), __startDateTime.timestamp() * 1000000, __endDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), __endDateTime.timestamp() * 1000000)
    __thisDate = __startDateTime.date()
    while __thisDate <= __endDateTime.date():
      if __thisDate == __endDateTime.date():
        __thisEndDateTime = __endDateTime
      else:
        __endDate = __startDateTime + timedelta(1)
        __thisEndDateTime = datetime(__endDate.year, __endDate.month, __endDate.day)
      self.__logger.debug("For %s to %s", __startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), __thisEndDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

      self.__logger.debug("Archive type '%s'", archive)
      self.requestData(archive, __startDateTime.strftime('%Y-%m-%d'), __startDateTime.timestamp() * 1000000 + 1, __endDateTime.timestamp() * 1000000)

      __thisDate = __thisDate + timedelta(1)
      __startDateTime = datetime.fromordinal(__thisDate.toordinal())

#############################################################################

#############################################################################
  def requestData(self, archivetype, date, _from, to=None, nexttimestamp=None):
    """
    Retrieves all data for a given request.  Note that this may involve many
    HTTP requests due to replies being too long, the server too busy, going
    over quota etc.
    """
    __url = self.__config["eddnarchive"]["baseurl"] + archivetype + "/" + date
    __headers = {"x-api-key":self.__config['eddnarchive']['apikey']}
    __limit = 500
    self.__backoff_sleep_start = self.__config['eddnarchive']['backoff']['basesleep']
    self.__backoff_sleep_multi = self.__config['eddnarchive']['backoff']['multiplier']
    self.__backoff_sleep_jitter = self.__config['eddnarchive']['backoff']['jitter']
    self.__backoff_sleep = self.__backoff_sleep_start
    self.__backoff_sleep_interquery = self.__backoff_sleep_start
    __params = {
      "limit": __limit,
      "from": '%.0f' % _from
    }
    if to:
      __params['to'] = '%.0f' % to
    if nexttimestamp:
      __params['nexttimestamp'] = nexttimestamp
    __data = []
    #################################################################
    __done = False
    while not __done:
      __params['limit'] = __limit
      self.__logger.debug("Requesting: '%s' with params: %s", __url, __params)
      try:
        self.__logger.debug("url = '%s', params = %s", __url, str(__params))
        __response = requests.get(__url, params=__params, headers=__headers, timeout=60.0)
        __json = __response.json()
        if __response.status_code != 200:
          if __json['message'] == 'body size is too long':
            __limit = max(1, __limit - 5)
            self.__logger.info("Got '%s', limit is now %d", __json['message'], __limit)
            sleep(self.__backoff_sleep_interquery)
          else:
            self.backoffSleep(__json['message'])
        elif __json.get('__type') and __json['__type'] == "" and __json.get('message') and re.match("^RequestId: [0-9a-f]+ Process exited before completing request", __json['message']):
          self.backoffSleep(__json['message'])
        else:
          #print(__response.json())
          self.__logger.debug("Got a valid response")
          ####################################################################
          for m in __json['Items']:
            (__eddn_message, __message_valid, __message_blacklisted, __message_schema_is_test) = validateEDDNMessage(m, self.__config, self.__logger)
            self.__db.insertMessage(__eddn_message.json, __message_blacklisted, __message_valid, __message_schema_is_test)
            self.__logger.info("Inserted message with gatewayTimeStamp: %s", __eddn_message.json['header']['gatewayTimestamp'])
          ####################################################################

          if __json.get('LastEvaluatedTimestamp'):
            self.__logger.info("Which had a LastEvaluatedTimestamp(%s), so setting nexttimestamp", __json['LastEvaluatedTimestamp'])
            __params['nexttimestamp'] = __json['LastEvaluatedTimestamp']
            sleep(self.__backoff_sleep_interquery)
          else:
            __done = True
            break
      except ConnectionError as Ex:
        self.__logger.error("Connection Error")
        self.backoffSleep("Connection Error")
      except HTTPError as Ex:
        self.__logger.error(__main__ + ": HTTPError")
      except Timeout as Ex:
        self.__logger.error(__main__ + ": Timeout")
      except TooManyRedirects as Ex:
        self.__logger.error(__main__ + ": TooManyRedirects")
      except ValueError as Ex:
        self.__logger.error(__main__ + ": ValueError (bad json?)")
    #################################################################
    return __data
#############################################################################

#############################################################################
  def backoffSleep(self, msg=None):
    if self.__backoff_sleep < self.__backoff_sleep_start:
      self.__logger.error("Erk, backoff_sleep now %f - how did that happen?", self.__backoff_sleep)
      return
    self.__logger.info("Encountered error '%s', sleeping for %f seconds...", msg, self.__backoff_sleep)
    sleep(self.__backoff_sleep)
    self.__backoff_sleep = max(
      self.__backoff_sleep_start * self.__backoff_sleep_multi,
      self.__backoff_sleep * self.__backoff_sleep_multi + randint(-1 * self.__backoff_sleep_jitter, self.__backoff_sleep_jitter)
    )
    self.__backoff_sleep_interquery += 1
#############################################################################
