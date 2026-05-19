############################
# STEP 1 build executable binary
############################
FROM golang:1.22.2

ENV GO111MODULE on
WORKDIR $GOPATH/src/github.com/lorenzodonini/ocpp-go
COPY . .
# Fetch dependencies.
RUN go mod download
# Build the binary.
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 \
    go build \
    -cover \
    -covermode=atomic \
    -coverpkg=./... \
    -o /csms \
    example/2.0.1/csms/*.go

RUN mkdir -p "/cover"
ENV GOCOVERDIR=/cover

RUN go install github.com/axw/gocov/gocov@latest
RUN go install github.com/AlekSi/gocov-xml@latest

# Ports on which the service may be exposed.
EXPOSE 8887
EXPOSE 443

ENTRYPOINT ["sh", "./start_server.sh"]
