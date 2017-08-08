#!/bin/sh

echo "SELECT d.datname AS Name,  pg_catalog.pg_get_userbyid(d.datdba) AS Owner, 
    CASE WHEN pg_catalog.has_database_privilege(d.datname, 'CONNECT')
        THEN pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname))
        ELSE 'No Access'
    END AS SIZE
FROM pg_catalog.pg_database d
    ORDER BY
    CASE WHEN pg_catalog.has_database_privilege(d.datname, 'CONNECT')
        THEN pg_catalog.pg_database_size(d.datname)
        ELSE NULL
    END DESC -- nulls first
    LIMIT 20
;
SELECT COUNT(*) FROM messages;
SELECT id,received FROM messages ORDER BY id ASC LIMIT 1;
SELECT id,received FROM messages ORDER BY id DESC LIMIT 1;" | psql --host=localhost --username eddnadmin --port=5433 --dbname=eddn
