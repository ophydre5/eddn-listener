#!/bin/sh

echo "SELECT DISTINCT date_trunc('minute', \"gatewaytimestamp\") AS minute, count(*) OVER (PARTITION BY date_trunc('minute', \"gatewaytimestamp\")) AS running_ct FROM messages ORDER BY 1;" \
	| psql \
			--host=localhost \
			--username eddnadmin \
			--port=5433 \
			--dbname=eddn
