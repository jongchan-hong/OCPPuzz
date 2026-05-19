FROM mcr.microsoft.com/mssql/server:2022-latest

USER root

ENV SA_PASSWORD="YourStrong@Password1!" \
    ACCEPT_EULA=Y \
    MSSQL_PID=Developer

ENV ACCEPT_EULA=Y \
    MSSQL_PID=Developer
ENV MSSQL_SA_PASSWORD=YourStrong@Password1!

RUN mkdir -p /logs/OCPP && \
    chown -R mssql /logs && \
    chmod -R 777 /logs
RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    apt-get remove -y libodbc2 libodbcinst2 unixodbc-common || true && \
    ACCEPT_EULA=Y apt-get install -y --allow-downgrades --allow-change-held-packages mssql-tools unixodbc-dev && \
    ln -s /opt/mssql-tools/bin/sqlcmd /usr/bin/sqlcmd && \
    rm -rf /var/lib/apt/lists/*

COPY ./SQL-Server /usr/src/app/SQL-Server
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
