#!/bin/bash
set -euo pipefail

SA_PASS="${MSSQL_SA_PASSWORD:-${SA_PASSWORD:-}}"
if [[ -z "${SA_PASS}" ]]; then
  echo "ERROR: MSSQL_SA_PASSWORD/SA_PASSWORD not set" >&2
  exit 1
fi

/opt/mssql/bin/sqlservr &

echo "Waiting for SQL Server to start..."
for i in {1..60}; do
  if /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "${SA_PASS}" -Q "SELECT 1" >/dev/null 2>&1; then
    echo "SQL Server is up."
    break
  fi
  sleep 2
  [[ $i -eq 60 ]] && { echo "ERROR: SQL Server did not become ready in time" >&2; exit 1; }
done

for f in /usr/src/app/SQL-Server/*.sql; do
  echo "Running $f..."
  /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "${SA_PASS}" -b -l 30 -i "$f" || true
done

wait -n