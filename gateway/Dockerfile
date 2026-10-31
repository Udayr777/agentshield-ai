FROM golang:1.24 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /gateway .
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /gateway /gateway
CMD ["/gateway"]
