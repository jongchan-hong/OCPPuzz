#!/bin/sh

PID=$(pgrep -f "/csms")

if [ -z "$PID" ]; then
  echo "app serve is not running."
  exit 1
fi

echo "Sending SIGTERM to app serve (PID=$PID)..."
kill -TERM "$PID"

sleep 1


go tool covdata textfmt -i=/cover -o coverage.out
gocov convert coverage.out | gocov-xml > coverage.xml