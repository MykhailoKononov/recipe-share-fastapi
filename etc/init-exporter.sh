set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE USER ${EXPORTER_USER} WITH PASSWORD '${EXPORTER_PASS}';
  GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${EXPORTER_USER};
  GRANT USAGE ON SCHEMA public TO ${EXPORTER_USER};
  GRANT SELECT ON pg_stat_activity, pg_stat_replication,
                 pg_stat_database, pg_locks,
                 pg_settings, pg_stat_bgwriter TO ${EXPORTER_USER};
  GRANT EXECUTE ON FUNCTION pg_catalog.pg_ls_waldir() TO ${EXPORTER_USER};
EOSQL