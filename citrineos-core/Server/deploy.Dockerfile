# Use a specific base image with platform support
FROM --platform=${BUILDPLATFORM:-linux/amd64} node:22 AS build

WORKDIR /usr/local/apps/citrineos

COPY . .
RUN npm run install-all && npm run build
RUN apt-get update && apt-get install -y vim curl lsof

# The final stage, which copies built files and prepares the run environment
# Using a slim image to reduce the final image size
FROM node:22-slim
COPY --from=build /usr/local/apps/citrineos /usr/local/apps/citrineos

WORKDIR /usr/local/apps/citrineos

EXPOSE ${PORT}
CMD sh -c "nohup npm run go-and-c8 > go-and-c8.log 2>&1 & tail -f go-and-c8.log"
