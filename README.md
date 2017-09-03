# eddn-listener
An EDDN listener, storing data into a postgresql database.

# Notes
If the relay is not receiving, and thus not sending, any data for a
while then you may see messages like:

2017-07-11 11:21:55.666 - eddnlistener - ERROR - eddnlistener.main: ZMQSocketException: Resource temporarily unavailable
2017-07-11 11:21:55.666 - eddnlistener - WARNING - eddnlistener.main: Disconnect from tcp://eddn.edcd.io:9500
2017-07-11 11:22:00.672 - eddnlistener - INFO - eddnlistener.main: Connect to tcp://eddn.edcd.io:9500

The frequency of these will be as per __timeoutEDDN.

The most common cause of this is the game servers being down for a
patch.
