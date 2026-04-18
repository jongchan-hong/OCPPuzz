docker-compose -p OCPP-core -f docker-compose-ocpp-core.yml up -d
docker-compose -p ocpp-go -f docker-compose-ocpp-go.yml up -d
docker-compose -p citrine -f citrineos-core/Server/docker-compose-directus.yml up -d
docker-compose -p maeve   -f maeve-csms/docker-compose.yml up -d