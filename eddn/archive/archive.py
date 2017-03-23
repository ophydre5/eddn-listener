import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout, TooManyRedirects
from time import sleep
from random import randint
import re
from datetime import datetime, timedelta

class archive:
  """
  Handles retrieving data from eddn-archive
  """

#############################################################################
  def __init__(self, config, logger):
    self.__config = config
    self.__logger = logger
#############################################################################

#############################################################################
  def getTimeRange(self, start, end=None):
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

    __data = []
    __thisDate = __startDateTime.date()
    while __thisDate <= __endDateTime.date():
      if __thisDate == __endDateTime.date():
        __thisEndDateTime = __endDateTime
      else:
        __endDate = __startDateTime + timedelta(1)
        __thisEndDateTime = datetime(__endDate.year, __endDate.month, __endDate.day)
      self.__logger.debug("Loop for %s to %s", __startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), __thisEndDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
      for a in self.__config['eddnarchive']['archivetypes']:
        self.__logger.debug("Loop for archive type '%s'", a)
        __data.extend(self.requestData("blackmarkets", __startDateTime.strftime('%Y-%m-%d'), __startDateTime.timestamp() * 1000000 + 1, __endDateTime.timestamp() * 1000000))
      __thisDate = __thisDate + timedelta(1)
      __startDateTime = datetime.fromordinal(__thisDate.toordinal())

    return __data
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
    __backoff_sleep_start = self.__config['eddnarchive']['backoff']['basesleep']
    __backoff_sleep_multi = self.__config['eddnarchive']['backoff']['multiplier']
    __backoff_sleep_jitter = self.__config['eddnarchive']['backoff']['jitter']
    __backoff_sleep = __backoff_sleep_start
    __backoff_sleep_interquery = __backoff_sleep_start
    __params = {
      "limit": __limit,
      "from": _from,
    }
    if to:
      __params['to'] = to
    if nexttimestamp:
      __params['nexttimestamp'] = nexttimestamp
    __data = []
    #################################################################
    while True:
      __params['limit'] = __limit
      self.__logger.debug("Requesting: '%s' with params: %s", __url, __params)
      try:
        __response = requests.get(__url, params=__params, headers=__headers, timeout=60.0)
        __json = __response.json()
        if __response.status_code != 200:
          if __json['message'] == 'body size is too long':
            __limit = max(1, __limit - 5)
          backoffSleep(__json['message'])
        elif __json.get('__type') and __json['__type'] == "" and __json.get('message') and re.match("^RequestId: [0-9a-f]+ Process exited before completing request", __json['message']):
          backoffSleep(__json['message'])
        else:
          #print(__response.json())
          __data.extend(__json['Items'])
          if __json.get('LastEvaluatedTimestamp'):
            __params['nexttimestamp'] = __json['LastEvaluatedTimestamp']
            sleep(__backoff_sleep_interquery)
          else:
            break
      except ConnectionError as Ex:
        self.__logger.error(__main__ + ": Connection Error")
        backoffSleep("Connection Error")
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
  def backoffSleep(msg=None):
    if __backoff_sleep < __backoff_sleep_start:
      self.__logger.error("Erk, backoff_sleep now %f - how did that happen?", __backoff_sleep)
      return
    self.__logger.info("Encountered error '%s', sleeping for %f seconds...", msg, __backoff_sleep)
    sleep(__backoff_sleep)
    __backoff_sleep = max(
      __backoff_sleep_start * __backoff_sleep_multi,
      __backoff_sleep * __backoff_sleep_multi + randint(-1 * __backoff_sleep_jitter, __backoff_sleep_jitter)
    )
    __backoff_sleep_interquery += 1
#############################################################################
