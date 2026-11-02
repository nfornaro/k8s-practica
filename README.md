# Práctica de Kubernetes

Material de la clase práctica de Kubernetes de Arquitectura de Software en la Práctica.
Los pasos, comandos y preguntas están en la guía de trabajo que entrega el equipo docente.

## Servicio de ejemplo

`pedidos` es un servicio HTTP mínimo en Python, sin dependencias. Escucha en el puerto 8080.

| Método | Ruta | Para qué sirve |
| --- | --- | --- |
| GET | `/hello` | Devuelve el Pod que respondió y la versión |
| GET | `/config` | Muestra la configuración que recibió el contenedor |
| GET | `/healthz` | Liveness probe |
| GET | `/readyz` | Readiness probe |
| GET | `/cpu?ms=200` | Consume CPU, para probar el autoescalado |
| POST | `/romper/listo` | Hace fallar la readiness de ese Pod |
| POST | `/arreglar/listo` | Revierte lo anterior |
| POST | `/romper/vivo` | Hace fallar la liveness de ese Pod |
| POST | `/crash` | Termina el proceso con error |

## Imágenes

| Imagen | Contenido |
| --- | --- |
| `ghcr.io/TU_USUARIO/pedidos:1.0.0` | Versión inicial |
| `ghcr.io/TU_USUARIO/pedidos:2.0.0` | Nueva versión sana |
| `ghcr.io/TU_USUARIO/pedidos:3.0.0` | Release roto: arranca, pero nunca queda listo |

## Estructura

```
app/app.py                  código del servicio
Dockerfile                  imagen del servicio
k8s/                        manifiestos, numerados según el paso de la guía
scripts/verificar.sh        recorre toda la práctica (uso docente)
```

## Construir la imagen por tu cuenta (opcional)

```bash
docker build -t pedidos:local --build-arg APP_VERSION=local .
docker run --rm -p 8080:8080 pedidos:local
curl localhost:8080/hello
```
