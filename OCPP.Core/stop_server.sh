#!/bin/bash

PID=$(ps aux | grep "dotnet OCPP.Core.Server.dll" | grep -v "dotnet-coverage" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "❌ dotnet OCPP.Core.Server.dll is not running."
  exit 1
fi

echo "🛑 Sending SIGINT to dotnet OCPP.Core.Server.dll (PID=$PID)..."
kill -15 "$PID"
