SELECT
	id,
	gatewaytimestamp,
	received,(commods->>'name') AS commod_name
FROM (
	SELECT
		id,
		gatewaytimestamp,
		received,
		jsonb_array_elements(message_search->'message'->'commodities') AS commods
	FROM messages
	WHERE
		gatewaytimestamp > timestamp '2017-08-22 00:00'
		AND message_search->>'$schemaref' = 'https://eddn.edcd.io/schemas/commodity/3'
) c
WHERE
	(commods->>'name') LIKE '%gold%'
ORDER BY gatewaytimestamp ASC;
