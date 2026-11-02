"""Servicio de pedidos de ejemplo para la práctica de Kubernetes.

Usa solo la biblioteca estándar de Python para que la imagen sea chica y el
código se pueda leer en un par de minutos.
"""

import json
import os
import signal
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", "8080"))
VERSION = os.environ.get("APP_VERSION", "dev")
# La versión 3.0.0 se construye con este flag para simular un release roto:
# el proceso arranca, pero nunca queda listo para recibir tráfico.
RELEASE_ROTO = os.environ.get("RELEASE_ROTO", "false") == "true"
STARTUP_DELAY = float(os.environ.get("STARTUP_DELAY_SECONDS", "3"))
SHUTDOWN_DELAY = float(os.environ.get("SHUTDOWN_DELAY_SECONDS", "3"))

HOSTNAME = socket.gethostname()
INICIO = time.monotonic()

estado = {"vivo": True, "listo": True}


def arranco():
    return time.monotonic() - INICIO >= STARTUP_DELAY


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "pedidos"

    def responder(self, codigo, cuerpo):
        datos = (json.dumps(cuerpo, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(datos)
        self.close_connection = True

    def do_GET(self):
        url = urlparse(self.path)
        ruta = url.path
        params = parse_qs(url.query)

        if ruta == "/hello":
            self.responder(200, {"message": f"Hola desde {HOSTNAME}", "version": VERSION})
        elif ruta == "/healthz":
            if estado["vivo"]:
                self.responder(200, {"vivo": True})
            else:
                self.responder(500, {"vivo": False})
        elif ruta == "/readyz":
            if not RELEASE_ROTO and estado["listo"] and arranco():
                self.responder(200, {"listo": True})
            else:
                self.responder(503, {"listo": False})
        elif ruta == "/config":
            self.responder(
                200,
                {
                    "pod": HOSTNAME,
                    "MENSAJE": os.environ.get("MENSAJE", "(sin configurar)"),
                    "MONEDA": os.environ.get("MONEDA", "(sin configurar)"),
                    "API_KEY_configurada": "API_KEY" in os.environ,
                },
            )
        elif ruta == "/cpu":
            self.responder(200, quemar_cpu(params))
        else:
            self.responder(404, {"error": "ruta inexistente", "ruta": ruta})

    def do_POST(self):
        ruta = urlparse(self.path).path
        if ruta == "/romper/listo":
            estado["listo"] = False
            self.responder(200, {"pod": HOSTNAME, "listo": False})
        elif ruta == "/arreglar/listo":
            estado["listo"] = True
            self.responder(200, {"pod": HOSTNAME, "listo": True})
        elif ruta == "/romper/vivo":
            estado["vivo"] = False
            self.responder(200, {"pod": HOSTNAME, "vivo": False})
        elif ruta == "/crash":
            self.responder(200, {"pod": HOSTNAME, "crash": True})
            threading.Timer(0.1, lambda: os._exit(1)).start()
        else:
            self.responder(404, {"error": "ruta inexistente", "ruta": ruta})

    def log_message(self, formato, *args):
        ruta = self.path.split("?")[0]
        if ruta in ("/healthz", "/readyz"):
            return
        print(f"{self.address_string()} {formato % args}", flush=True)


def quemar_cpu(params):
    try:
        milisegundos = int(params.get("ms", ["100"])[0])
    except ValueError:
        milisegundos = 100
    milisegundos = max(0, min(milisegundos, 2000))
    fin = time.monotonic() + milisegundos / 1000
    acumulado = 0
    while time.monotonic() < fin:
        acumulado += sum(i * i for i in range(1000))
    return {"pod": HOSTNAME, "ms": milisegundos}


def main():
    servidor = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    servidor.daemon_threads = True

    def apagar(numero, _frame):
        # Sigue atendiendo unos segundos: el Service tarda un instante en dejar
        # de enviarle tráfico a este Pod.
        print(f"Señal {signal.Signals(numero).name}: me preparo para apagar", flush=True)
        estado["listo"] = False
        threading.Timer(SHUTDOWN_DELAY, servidor.shutdown).start()

    signal.signal(signal.SIGTERM, apagar)
    signal.signal(signal.SIGINT, apagar)

    print(f"pedidos {VERSION} escuchando en :{PORT} (pod {HOSTNAME})", flush=True)
    servidor.serve_forever()
    print("Apagado limpio", flush=True)


if __name__ == "__main__":
    main()
