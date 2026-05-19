# syntax=docker/dockerfile:1.2

# STAGE 1: build the executable with coverage
FROM golang:1.22.2 AS builder
ENV GOFLAGS="-tags=nocover"
RUN apt-get update && apt-get install -y git openssh-client ca-certificates curl

ARG TARGETARCH

# Fix for arm64 static curl
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        TARGETARCH=aarch64 ; \
    fi; \
    wget -O /usr/bin/curl https://github.com/moparisthebest/static-curl/releases/download/v8.0.1/curl-$TARGETARCH \
    && chmod +x /usr/bin/curl

WORKDIR /src

COPY ./go.mod ./go.sum ./
RUN go mod download

COPY ./ ./

# Build with coverage enabled
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 \
    go build \
    -cover \
    -covermode=atomic \
    -coverpkg=$(go list ./... | grep -vE '(has2be|ocpp16|ocpi|adminui|cmd|inmemory|firestore|mqtt|ocpp/ocpp201|services)' | tr '\n' ',' | sed 's/,$//') \
    -o /app \
    .

# Install coverage tools
RUN go install github.com/axw/gocov/gocov@latest
RUN go install github.com/AlekSi/gocov-xml@latest

# STAGE 2: runtime container
FROM golang:1.22.2 AS final

# Install runtime dependencies
RUN apt-get update && apt-get install -y ca-certificates curl

COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /app /app
COPY --from=builder /go/bin/* /usr/local/bin/

# Coverage directory
RUN mkdir -p "/cover"
ENV GOCOVERDIR=/cover

# Copy start and stop scripts
COPY ./start_server.sh ./stop_server.sh ./

# Non-root user (optional)
RUN useradd -u 10000 -m appuser
USER appuser

ENTRYPOINT ["sh", "./start_server.sh"]

#github.com/thoughtworks/maeve-csms/manager/store/firestore/ocpi.go
#github.com/thoughtworks/maeve-csms/manager/server/ocpi.go:71.2,71.22 1 0
#github.com/thoughtworks/maeve-csms/manager/ocpp/ocpp16/trigger_message.go:13.41,13.42 0 0
#github.com/thoughtworks/maeve-csms/manager/ocpi/ocpi.go:149.65,165.2 2 0
#github.com/thoughtworks/maeve-csms/manager/ocpi/ocpi.go:167.75,169.16 2 0
#github.com/thoughtworks/maeve-csms/manager/ocpi/ocpi.gen.go:12611.2,12611.8 1 1
#github.com/thoughtworks/maeve-csms/manager/handlers/ocpp16/trigger_message_result.go:29.2,29.12 1 0
#github.com/thoughtworks/maeve-csms/manager/handlers/has2be/authorize.go:17.128,27.44 3 0
#
#has2be
#ocpp16
#ocpi
#ocpp16
#ocpi.go