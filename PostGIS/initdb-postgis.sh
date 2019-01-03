#!/bin/sh

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Create the 'spdb_postgis' template db
"${psql[@]}" <<- 'EOSQL'
CREATE DATABASE spdb_postgis;
UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'spdb_postgis';
EOSQL

# Load PostGIS into both spdb_database and $POSTGRES_DB
for DB in spdb_postgis "$POSTGRES_DB"; do
	echo "Loading PostGIS extensions into $DB"
	"${psql[@]}" --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION IF NOT EXISTS postgis;
		CREATE EXTENSION IF NOT EXISTS postgis_topology;
		CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
		CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
                CREATE EXTENSION IF NOT EXISTS pgrouting;
EOSQL
done

# Load Maps data into spdb_postgis
echo "Loading Maps data into $DB"
"${psql[@]}" --dbname="$POSTGRES_DB" --file=/psql-data/hh_2po_4pgr.sql
echo "Maps data loaded"
