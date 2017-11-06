#!/bin/sh

echo "DELETE FROM messages WHERE gatewaytimestamp < (CURRENT_TIMESTAMP - interval '40 days');" \
	| psql \
			--host=localhost \
			--username eddnadmin \
			--port=5433 \
			--dbname=eddn

df -h /home/postgresql
