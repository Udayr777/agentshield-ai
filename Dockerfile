FROM node:22-alpine AS ui
WORKDIR /build
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

FROM golang:1.24 AS gateway
WORKDIR /build
COPY gateway/ ./
RUN CGO_ENABLED=0 go build -buildvcs=false -o /gateway .

FROM python:3.12-slim
WORKDIR /app
COPY agent/requirements.txt ./agent/requirements.txt
RUN pip install --no-cache-dir -r agent/requirements.txt && useradd --create-home shield
COPY agent/ ./agent/
COPY samples/ ./samples/
COPY --from=ui /build/dist ./dashboard/dist
COPY --from=gateway /gateway ./gateway/gateway
COPY scripts/serve-cloud.py ./scripts/serve-cloud.py
RUN chown -R shield:shield /app
USER shield
ENV PYTHONUNBUFFERED=1 STATIC_DIR=/app/dashboard/dist
EXPOSE 10000
CMD ["python","scripts/serve-cloud.py"]
