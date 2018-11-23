SELECT
	DISTINCT date_trunc('minute', "gatewaytimestamp") AS minute,
	count(*) OVER (PARTITION BY date_trunc('minute', "gatewaytimestamp")) AS count
FROM messages
	WHERE gatewaytimestamp > date_trunc('hour', NOW())
ORDER BY 1 DESC
	LIMIT 10;
