FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /app
COPY . .
RUN dotnet restore
RUN dotnet build -c Release
RUN dotnet publish -c Release -o out

RUN mkdir -p /logs/OCPP && \
    chmod -R 777 /logs

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/out ./
EXPOSE 8082
ENTRYPOINT ["dotnet", "OCPP.Core.Management.dll"]