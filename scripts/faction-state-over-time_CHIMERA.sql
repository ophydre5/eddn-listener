SELECT id,gatewaytimestamp,starsystem,(factions->>'Name') as factionname,(factions->>'FactionState') AS factionstate,(factions->>'PendingStates') AS pendingstates, (factions->>'RecoveringStates') AS recoveringstates FROM
	(
		SELECT id, gatewaytimestamp, message->'message'->>'StarSystem' AS starsystem, jsonb_array_elements(message->'message'->'Factions') as factions FROM messages
		WHERE
			message->'message'->>'StarSystem' IN
				(
					'Amy-Charlotte',
					'Arebelatja',
					'Baliscii',
					'Bella',
					'Carii',
					'Daurtu',
					'Forsha',
					'Guanatamas',
					'HIP 25880',
					'HIP 26933',
					'HIP 32806',
					'Kamuti',
					'LTT 11926',
					'Mbeguenchu',
					'Mukun',
					'Niu Benzai',
					'Pongkala',
					'Rutena',
					'Selgeth',
					'Sharijio',
					'Sui Redd',
					'Tofana',
					'Utero',
					'Wakait',
					'Watiwati',
					'Wikmeang Mu',
					'Yun Dun'
				)
	) f ORDER BY gatewaytimestamp ASC;
