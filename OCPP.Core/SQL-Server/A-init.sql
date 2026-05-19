IF DB_ID(N'OCPP.Core') IS NULL
BEGIN
  PRINT 'Creating database [OCPP.Core]';
  CREATE DATABASE [OCPP.Core];
END
ELSE
BEGIN
  PRINT 'Database [OCPP.Core] already exists. Skipping creation.';
END
GO