SELECT id,gatewaytimestamp,starsystem,(factions->>'Name') as factionname,(factions->>'FactionState') AS factionstate,(factions->>'PendingStates') AS pendingstates FROM
	(
		SELECT id, gatewaytimestamp, message->'message'->>'StarSystem' AS starsystem, jsonb_array_elements(message->'message'->'Factions') as factions FROM messages
		WHERE
			message->'message'->>'StarSystem' = 'LTT 4961'
	) f ORDER BY gatewaytimestamp ASC;
