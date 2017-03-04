# eddn-listener
An EDDN listener, storing data into a database.

The intention is to both store the raw messages and also some more
detail, in extra DB columns, in order to make the data quickly
searchable.

There will also be an off-line process to delete data older than a
certain number of days to keep storage requirements down.
