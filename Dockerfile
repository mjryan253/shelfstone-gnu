# Stage 1: Build the Go application
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Copy go.mod and go.sum first to leverage Docker cache
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the application source code
COPY . .

# Build the application
# CGO_ENABLED=0 is important for a statically linked binary if using Alpine as the base image
# and also helps if Calibre's CLI tools are not dynamically linked in the final image.
# However, since we expect Calibre to be installed on the host or a separate container,
# we might not need to worry about its dependencies as much for the Go binary itself.
# For now, we'll build a standard dynamic binary.
RUN go build -o /shelfstone main.go

# Stage 2: Create the final lightweight image
FROM alpine:latest

# Install Calibre. This is a large dependency.
# Consider if Calibre should be in a separate container or if the host must provide it.
# For this phase, we'll install it in the same container.
# This will significantly increase the image size and build time.
RUN apk add --no-cache calibre

WORKDIR /app

# Copy the built application from the builder stage
COPY --from=builder /shelfstone /app/shelfstone

# Create directories for books, data, covers, and processed ebooks
# These will ideally be mapped to volumes in docker-compose
RUN mkdir -p /app/books && \
    mkdir -p /app/data/covers && \
    mkdir -p /app/data/processed_ebooks

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
# The expectation is that the /app/books volume will be mounted from the host.
# The database will be created in /app/data/
ENTRYPOINT ["/app/shelfstone"]
