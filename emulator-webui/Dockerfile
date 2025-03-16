# syntax=docker/dockerfile:1-labs

# -------- STEP 1: Frontend --------
FROM denoland/deno:latest AS frontend

WORKDIR /app/frontend
COPY . .

# install dependencies
RUN deno install --allow-scripts

# build the frontend
ENV VITE_MQTT_HOST=127.0.0.1
ENV VITE_MQTT_PORT=8083
RUN deno run build --outDir dist

# -------- STEP 2: Backend --------
FROM halverneus/static-file-server:latest AS backend

# copy the frontend build to the backend
COPY --from=frontend /app/frontend/dist /web
