# Análisis de capacidad

## Escenarios de prueba planteados:

### Escenario 1 - Capacidad de la capa Web (usuarios concurrentes)
Determinar el número de usuarios concurrentes que la API de subida soporta cumpliendo SLOs, sin estar limitado por la capa asíncrona.

### Estrategia de implementación
Se desacopló la capa de procesamiento asíncrono para la realización de estas pruebas. 
De esta forma, la capa Web no se ve limitada por la capacidad de procesamiento de los videos. 
Para esto se ejecutan las pruebas sin la activación del proceso de Celery, 
el cuál se encarga de orquestar las tareas asíncronas de procesamiento de video con la cola de mensajería.

### Escenarios de prueba
* **Sanidad (Smoke):** 5 usuarios durante 1 minutos para validar que todo responde y la telemetría está activa.
* **Escalamiento rápido (Ramp):** iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 100 → 150 → 200) hasta observar degradación.
* **Sostenida corta:** ejecutar 5 minutos en el 80% de X (el mejor nivel previo sin degradación) para confirmar estabilidad.

### Criterios de éxito/fallo
Capacidad máxima, mayor número de usuarios concurrentes que cumple:
* p95 de endpoints ≤ 1 s
* Errores (4xx evitables/5xx) ≤ 5%.
* Sin resets/timeouts anómalos ni throttling del almacenamiento.

### Herramientas utilizadas
* Generador: JMeter
* Observabilidad: Prometheus/Grafana

### Salidas esperadas
* Curva usuarios→latencia/errores.
* RPS sostenido a capacidad máxima.
* Bottlenecks con evidencias.

## Resultados

* Se crearon 3 treads de usuarios en JMeter, cada uno enviando peticiones de subida de video de aproximadamente 8MB de tamaño; de acuerdo a cada escenario de prueba.
* El archivo plantilla en Jmeter se encuentra en el repositorio en la ruta: `capacity_planning/HTTP_Request_cargar_videos.jmx`
* Al realizar la prueba de escalamiento rápido, se encontró que la capa web soporta hasta 100 usuarios concurrentes sin presentar degradación. El 97% de las peticiones presentaron respuesta exitosa y una latencia de 1000ms.
* A partir de 150 usuarios, se empiezan a observar errores 500 en las respuestas, y la latencia de las peticiones empieza a aumentar hasta llegar a un punto máximo de 30 segundos.
* A continuación se presentan los gráficos de la ejecución de la prueba.
