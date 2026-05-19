# INSTALL

## Environment Requirements

- Ubuntu 22.04 LTS
- Python 3.13+
- Docker
- Docker Compose
- ODBC Driver 17 for SQL Server

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Start OCPPuzz Infrastructure

```bash
docker-compose -p OCPPuzz -f docker-compose.yml up -d
```

---

## Build Target CSMS

### Build All CSMS

```bash
./csms-docker-compose.sh
```

### Build Specific CSMS

```bash
# citrine CSMS
docker-compose -p citrine -f citrineos-core/Server/docker-compose-directus.yml up -d

# OCPP-core CSMS
docker-compose -p OCPP-core -f docker-compose-ocpp-core.yml up -d

# ocpp-go CSMS
docker-compose -p ocpp-go -f docker-compose-ocpp-go.yml up -d

# maeve CSMS
docker-compose -p maeve -f maeve-csms/docker-compose.yml up -d
```

---

## Verify Installation

Check Docker containers:

```bash
docker ps
```

Expected containers:
- ocppuzz
  - kafka
  - db
  - zookeeper
- target CSMS containers