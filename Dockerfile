FROM python:3.13-alpine

ARG APP_VERSION=dev
ARG RELEASE_ROTO=false
ENV APP_VERSION=${APP_VERSION} \
    RELEASE_ROTO=${RELEASE_ROTO} \
    PYTHONUNBUFFERED=1

# curl queda en la imagen para poder probar el servicio desde adentro de un Pod.
RUN apk add --no-cache curl

WORKDIR /app
COPY app/app.py .

USER 1000:1000
EXPOSE 8080
CMD ["python", "app.py"]
