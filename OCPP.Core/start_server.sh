#!/bin/bash
set -e

dotnet-coverage collect \
  --output /app/coverage.cobertura.xml \
  --output-format cobertura \
  --filter "-[OCPP.Core.Server.ControllerOCPP16]*" \
  --filter "-[OCPP.Core.Server.Messages_OCPP16]*" \
  --filter "-[OCPP.Core.Server.OCPPMiddleware]*<*16*>*" \
  --filter "-[OCPP.Core.Server.ExtensionLoadContext]*" \
  --filter "-[OCPP.Core.Database.Migrations]*" \
  -- \
  dotnet OCPP.Core.Server.dll