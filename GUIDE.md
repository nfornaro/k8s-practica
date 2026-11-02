# Guía de Trabajo: Kubernetes en la práctica

Arquitectura de Software en la Práctica

## Objetivo

En estas dos horas van a desplegar, romper, actualizar y escalar un microservicio en un cluster local. El objetivo no es memorizar comandos, sino conectar lo que hace Kubernetes con las decisiones de arquitectura vistas en el teórico.

El servicio de ejemplo es `pedidos`, el mismo que aparece en las slides de arquitecturas de microservicios.

## Cómo trabajar

- **En parejas.** Una persona ejecuta y la otra predice e interpreta. Roten en cada paso.
- **Predecir antes de ejecutar.** Donde la guía dice "Predecir", escriban la respuesta antes de correr el comando. Equivocarse es parte de la práctica.
- **Respuestas cortas.** Alcanza con dos o tres oraciones por pregunta. Se entregan en un documento con las capturas que se piden.
- **Si algo falla.** Miren primero `kubectl describe pod <nombre>` y `kubectl logs <nombre>`. Si no se resuelve, dejen evidencia del error, respondan las preguntas igual y sigan con el próximo paso.
- **Dos terminales.** La terminal A queda observando el cluster y la terminal B ejecuta comandos. Desde el paso 6 suman una terminal C para generar tráfico.
- **Windows.** Usen PowerShell o Git Bash. Algunos comandos no funcionan en `cmd`.

Todos los comandos se ejecutan desde la carpeta del repositorio. Donde dice `<pod>`, reemplacen por el nombre de un Pod que vean en `kubectl get pods`.

## Cronograma

| Paso | Tema | Minutos | Termina en |
| --- | --- | --- | --- |
| 1 | Explorar el cluster | 15 | 0:15 |
| 2 | Correr un Pod | 10 | 0:25 |
| 3 | Deployment y auto-remediación | 15 | 0:40 |
| 4 | Service y descubrimiento | 15 | 0:55 |
| 5 | Configuración externa | 10 | 1:05 |
| 6 | Probes | 15 | 1:20 |
| 7 | Rolling update y rollback | 15 | 1:35 |
| 8 | Autoescalado | 15 | 1:50 |
| 9 | Cierre: ¿cuándo usar Kubernetes? | 10 | 2:00 |

## Antes de la clase

Hagan esta preparación en casa, porque descarga varios cientos de MB y la red del salón no alcanza para todos a la vez. Lleva entre 20 y 30 minutos.

1. Instalar [Docker](https://docs.docker.com/get-started/get-docker/), [kubectl](https://kubernetes.io/docs/tasks/tools/) y [minikube](https://minikube.sigs.k8s.io/docs/start/).
2. Levantar el cluster y habilitar las métricas, que se usan en el paso 8:

```bash
minikube start
minikube addons enable metrics-server
```

3. Clonar el repositorio de la práctica:

```bash
git clone https://github.com/TU_USUARIO/k8s-practica.git
cd k8s-practica
```

4. Descargar las imágenes dentro del cluster:

```bash
minikube image pull ghcr.io/TU_USUARIO/pedidos:1.0.0
minikube image pull ghcr.io/TU_USUARIO/pedidos:2.0.0
minikube image pull ghcr.io/TU_USUARIO/pedidos:3.0.0
```

5. Comprobar que el nodo aparece en estado `Ready`:

```bash
kubectl get nodes
```

El día de la clase, antes de empezar, alcanza con ejecutar `minikube start`. Si no logran completar la preparación, avisen antes de la clase para trabajar con otra pareja.

## Paso 1: Explorar el cluster (15 min.)

Un cluster no es una caja negra: sus propios componentes se pueden ver con las mismas herramientas que usarán para su aplicación.

```bash
kubectl get nodes -o wide
kubectl get namespaces
kubectl get pods -n kube-system
```

Busquen en la salida los componentes del control plane y de los nodos que vieron en el teórico.

**Pregunta 1.** ¿Qué Pod corresponde a cada componente del control plane? Uno de los componentes del teórico no aparece: ¿cuál es y por qué no hace falta acá?

**Pregunta 2.** En minikube, el control plane y las aplicaciones comparten un solo nodo. ¿Qué riesgo tendría esto en producción? ¿Qué parte de este problema resuelve contratar EKS, AKS o GKE?

**Pregunta 3.** Predecir: si el `kube-apiserver` se cae durante unos minutos, ¿los usuarios de una aplicación ya desplegada dejan de recibir servicio? ¿Qué es lo que sí deja de funcionar?

## Paso 2: Correr un Pod (10 min.)

Abran `k8s/02-pod.yaml` e identifiquen `apiVersion`, `kind`, `metadata` y `spec`. Luego ejecuten:

```bash
kubectl apply -f k8s/02-pod.yaml
kubectl get pods -o wide
kubectl describe pod pedidos-pod
kubectl logs pedidos-pod
kubectl exec pedidos-pod -- curl -s localhost:8080/hello
```

Incluyan una captura de la respuesta de `/hello` en la entrega.

**Pregunta 4.** Miren la sección `Events` de `describe`. ¿Qué componente de la arquitectura generó cada evento? Con esto, describan el recorrido desde `kubectl apply` hasta el contenedor corriendo.

**Pregunta 5.** Predecir: ¿qué va a pasar con el Pod si lo borramos? Después compruébenlo:

```bash
kubectl delete pod pedidos-pod
kubectl get pods
```

**Pregunta 6.** Las slides dicen que el Pod es la unidad mínima de trabajo. Según lo que acaban de ver, ¿por qué casi nunca se crea un Pod directamente en producción?

## Paso 3: Deployment y auto-remediación (15 min.)

En la terminal A, dejen observando los Pods:

```bash
kubectl get pods -w
```

En la terminal B, creen el Deployment y miren qué objetos aparecieron:

```bash
kubectl apply -f k8s/03-deployment.yaml
kubectl get deployment,replicaset,pods
```

**Pregunta 7.** Comparen los nombres de los tres tipos de objeto. ¿Quién crea a quién? ¿Qué responsabilidad tiene cada nivel?

Ahora provoquen dos fallas distintas, mirando la terminal A en cada una:

```bash
kubectl delete pod <pod>
kubectl exec <pod> -- curl -s -X POST localhost:8080/crash
kubectl get pods
```

**Pregunta 8.** En un caso apareció un Pod nuevo y en el otro aumentó `RESTARTS`. ¿Qué componente reaccionó en cada caso y qué pasó con el nombre del Pod? ¿Qué se pierde en cada uno si la aplicación guarda datos en memoria?

Por último, comparen las dos formas de escalar. Cambien `replicas: 4` por `replicas: 6` en `k8s/03-deployment.yaml` y ejecuten:

```bash
kubectl apply -f k8s/03-deployment.yaml
kubectl scale deployment pedidos --replicas=2
kubectl get deployment pedidos
```

**Pregunta 9.** Ahora el archivo dice 6 réplicas y el cluster tiene 2. ¿Cuál de los dos es la fuente de verdad? ¿Qué problemas trae esta diferencia en un equipo de varias personas? Vuelvan a ejecutar `kubectl apply` y expliquen qué pasó.

## Paso 4: Service y descubrimiento (15 min.)

Los Pods van y vienen, y su IP cambia. Creen un Service y un Pod `cliente`, que representa a otro microservicio del cluster:

```bash
kubectl apply -f k8s/04-service.yaml -f k8s/04-cliente.yaml
kubectl get service pedidos
kubectl get endpointslices -l kubernetes.io/service-name=pedidos
kubectl get pods -l app=pedidos -o wide
```

Cuando `cliente` esté `Running`, llamen al servicio por su nombre varias veces:

```bash
kubectl exec cliente -- sh -c 'for i in 1 2 3 4 5 6 7 8 9 10; do curl -s http://pedidos/hello; done'
```

**Pregunta 10.** ¿Quién responde en cada llamada? ¿Cuál de las preguntas de la slide "Hay que preguntarse" resuelve esto? ¿Qué pasaría si `cliente` tuviera configurada la IP de un Pod?

Predecir: ¿qué va a pasar si le cambiamos la etiqueta `app` a uno de los Pods? Después compruébenlo y repitan la llamada anterior:

```bash
kubectl label pod <pod> app=retirado --overwrite
kubectl get pods --show-labels
```

**Pregunta 11.** ¿Cuántos Pods hay ahora y por qué? Con esto, expliquen qué vincula a un Service y a un ReplicaSet con sus Pods. ¿Qué ventaja y qué riesgo tiene este acoplamiento? Al terminar, borren el Pod retirado.

Por último, accedan desde su máquina. Ejecuten el siguiente comando y abran `http://localhost:8080/hello` en el navegador, recargando varias veces:

```bash
kubectl port-forward service/pedidos 8080:80
```

**Pregunta 12.** ¿Por qué ahora siempre responde el mismo Pod? `port-forward` es una herramienta de diagnóstico. Mirando la slide "Producto digital en k8s", ¿cómo llegaría un usuario real a `pedidos`? ¿Qué servicios del diagrama expondrían hacia afuera?

Corten el `port-forward` con Ctrl+C antes de seguir.

## Paso 5: Configuración externa (10 min.)

La misma imagen debe poder correr en distintos ambientes. Apliquen la configuración y consulten qué recibió el contenedor:

```bash
kubectl apply -f k8s/05-config.yaml -f k8s/05-deployment.yaml
kubectl rollout status deployment/pedidos
kubectl exec cliente -- curl -s http://pedidos/config
```

Cambien `MONEDA` a `USD` en `k8s/05-config.yaml`. Predecir: ¿`/config` va a mostrar el valor nuevo después de aplicar el cambio? Compruébenlo:

```bash
kubectl apply -f k8s/05-config.yaml
kubectl exec cliente -- curl -s http://pedidos/config
```

Luego reinicien los Pods de forma ordenada y vuelvan a consultar:

```bash
kubectl rollout restart deployment/pedidos
kubectl rollout status deployment/pedidos
kubectl exec cliente -- curl -s http://pedidos/config
```

**Pregunta 13.** ¿Por qué no se aplicó el cambio hasta reiniciar? ¿Qué ventaja tiene no construir una imagen distinta por ambiente?

Ahora miren el Secret:

```bash
kubectl get secret pedidos-secret -o jsonpath="{.data.API_KEY}" | base64 -d
```

**Pregunta 14.** ¿Qué protección da un Secret por sí solo frente a un ConfigMap? En este repositorio el valor está versionado en Git: ¿qué harían distinto en un sistema real?

## Paso 6: Probes (15 min.)

Un proceso corriendo no es lo mismo que un servicio sano. Apliquen la versión con probes del Deployment y lean la configuración de `readinessProbe` y `livenessProbe` en `k8s/06-deployment.yaml`:

```bash
kubectl apply -f k8s/06-deployment.yaml
kubectl rollout status deployment/pedidos
```

En la terminal A mantengan `kubectl get pods -w`. En la terminal C, generen tráfico continuo:

```bash
kubectl exec -it cliente -- sh -c 'while true; do curl -s -m 2 http://pedidos/hello || echo FALLO; sleep 1; done'
```

Predecir: ¿qué va a pasar con el Pod si falla su readiness? ¿Y con el tráfico? Después hagan fallar a uno y observen unos 20 segundos:

```bash
kubectl exec <pod> -- curl -s -X POST localhost:8080/romper/listo
```

Repárenlo y hagan fallar su liveness:

```bash
kubectl exec <pod> -- curl -s -X POST localhost:8080/arreglar/listo
kubectl exec <pod> -- curl -s -X POST localhost:8080/romper/vivo
```

Cuando se reinicie, lean los eventos con `kubectl describe pod <pod>`.

**Pregunta 15.** Completen con lo que observaron: para cada probe que falla, ¿qué pasa con `READY`, con `RESTARTS` y con el tráfico?

**Pregunta 16.** `pedidos` depende de una base de datos. Si la base se cae, ¿qué pasaría si la liveness la verificara? ¿Y si la verificara la readiness? ¿Qué debería chequear cada probe?

**Pregunta 17.** Los manifiestos anteriores no tenían probes. ¿Qué haría Kubernetes con un Pod cuyo proceso sigue vivo pero devuelve errores? ¿Qué parte de la resiliencia resuelve la plataforma y qué parte le toca al equipo que desarrolla el servicio?

## Paso 7: Rolling update y rollback (15 min.)

Dejen el tráfico corriendo en la terminal C. Lean `maxSurge` y `maxUnavailable` en `k8s/06-deployment.yaml`.

**Pregunta 18.** Predecir: con 4 réplicas, ¿cuál es la mínima cantidad de Pods disponibles y la máxima cantidad total durante una actualización? ¿Qué decisión de negocio refleja cada parámetro?

Cambien la imagen en `k8s/06-deployment.yaml` a la versión `2.0.0` y apliquen:

```bash
kubectl apply -f k8s/06-deployment.yaml
kubectl rollout status deployment/pedidos
kubectl get replicaset
kubectl rollout history deployment/pedidos
```

Miren en la terminal C qué versión responde y si aparece algún `FALLO`. Incluyan una captura donde se vean respuestas de las dos versiones.

**Pregunta 19.** Durante unos segundos conviven las dos versiones atendiendo usuarios. ¿Qué exige esto del diseño de la API y de los cambios en la base de datos? Den un ejemplo de un cambio que rompería con esta estrategia.

Ahora desplieguen un release roto. Cambien la imagen a la versión `3.0.0` y apliquen:

```bash
kubectl apply -f k8s/06-deployment.yaml
kubectl rollout status deployment/pedidos --timeout=40s
kubectl get pods
kubectl get deployment pedidos
```

**Pregunta 20.** ¿El despliegue terminó? ¿Qué versión ven los usuarios en la terminal C? ¿Qué mecanismo los protegió y qué costo tuvo en capacidad? ¿Qué habría pasado sin readiness?

Vuelvan atrás:

```bash
kubectl rollout undo deployment/pedidos
kubectl rollout status deployment/pedidos
```

**Pregunta 21.** Después del `undo`, ¿qué versión dice el archivo y qué versión corre en el cluster? ¿Cómo debería reflejarse un rollback en un flujo de entrega continua? Dejen el archivo en `2.0.0` antes de seguir y corten el tráfico de la terminal C.

## Paso 8: Autoescalado (15 min.)

El HPA ajusta las réplicas según la carga, usando un porcentaje de los `requests` de CPU. Vean el consumo actual y creen el autoescalador:

```bash
kubectl top pods -l app=pedidos
kubectl apply -f k8s/08-hpa.yaml
```

En la terminal A, reemplacen lo que estaban observando por:

```bash
kubectl get hpa pedidos -w
```

Si `TARGETS` muestra `<unknown>`, esperen un minuto. Predecir: sin carga, ¿cuántas réplicas van a quedar? Cuando se estabilice, generen carga y observen unos 2 o 3 minutos:

```bash
kubectl apply -f k8s/08-carga.yaml
```

Incluyan una captura de la columna `REPLICAS` subiendo. Luego quiten la carga y observen cómo baja:

```bash
kubectl delete deployment carga
```

**Pregunta 22.** ¿Cuánto tardó en reaccionar? Si un pico de tráfico llega en 10 segundos, ¿alcanza con el HPA? ¿Qué otras decisiones ayudarían y cuánto cuestan?

**Pregunta 23.** `pedidos` escala a 8 réplicas, pero todas usan la misma base de datos. ¿Dónde aparece el próximo cuello de botella? ¿Qué condiciones debe cumplir un servicio para escalar horizontalmente?

**Pregunta 24.** `k8s/06-deployment.yaml` sigue declarando `replicas: 4`. ¿Qué pasaría si alguien lo vuelve a aplicar mientras el HPA tiene 8 réplicas? ¿Cómo lo resolverían en el manifiesto?

## Paso 9: Cierre (10 min.)

**Pregunta 25.** Completen la tabla con lo que hicieron hoy. Si una propiedad no se pudo comprobar en esta práctica, digan qué habría que hacer para comprobarla.

| Propiedad cloud native | Mecanismo que usamos | Paso y evidencia |
| --- | --- | --- |
| Resiliencia |  |  |
| Escalabilidad |  |  |
| Entrega continua |  |  |
| Configuración externa |  |  |
| Infraestructura declarativa |  |  |
| Portabilidad |  |  |

**Pregunta 26.** Como arquitectos, ¿recomendarían Kubernetes en cada caso? Justifiquen con un beneficio y un costo concretos, y propongan una alternativa si la descartan.

- **Caso A.** Una startup de 4 desarrolladores, con un monolito y tráfico estable.
- **Caso B.** Un marketplace de 40 desarrolladores, con 25 servicios que se despliegan por separado y picos fuertes en fechas de promoción.
- **Caso C.** Un equipo de 6 desarrolladores, con 3 servicios sin estado y tráfico muy variable, sin nadie dedicado a operar infraestructura.

**Pregunta 27.** Hoy desplegaron un servicio que se actualiza, se recupera y escala solo. Nombren tres cosas que todavía le faltan para llegar a producción. ¿Cuáles de ellas resolvería Kubernetes y cuáles no?

## Limpieza

```bash
kubectl delete -f k8s/ --ignore-not-found
minikube stop
```

Para liberar espacio en disco cuando ya no lo necesiten, ejecuten `minikube delete`.

## Si terminan antes

- **Construir su propia imagen.** Modifiquen el mensaje en `app/app.py`, ejecuten `docker build -t pedidos:local --build-arg APP_VERSION=local .` y `minikube image load pedidos:local`, y desplieguen esa imagen en el Deployment.
- **Startup probe.** Agreguen la variable `STARTUP_DELAY_SECONDS` con valor `30` al contenedor y observen qué pasa con el Pod. Luego agreguen una `startupProbe` adecuada y expliquen en qué caso sería indispensable.
- **Otro tipo de Service.** Cambien el tipo del Service a `NodePort` y accedan con `minikube service pedidos --url`. ¿Qué diferencia hay con `port-forward`?
