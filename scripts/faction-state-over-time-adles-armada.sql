SELECT id,gatewaytimestamp,starsystem,(factions->>'Name') as factionname,(factions->>'FactionState') AS factionstate,(factions->>'PendingStates') AS pendingstates FROM
	(
		SELECT id, gatewaytimestamp, message->'message'->>'StarSystem' AS starsystem, jsonb_array_elements(message->'message'->'Factions') as factions FROM messages
		WHERE
			gatewaytimestamp > timestamp '2017-06-26 00:00:00'
			AND message->'message'->>'StarSystem' = 'Eravate'
	) f ORDER BY gatewaytimestamp ASC;
