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
* Curva usuarios→latencia/errores/exitos.
* RPS sostenido a capacidad máxima.
* Bottlenecks con evidencias.

## Resultados

* Se crearon 3 treads de usuarios en JMeter, cada uno enviando peticiones de subida de video de aproximadamente 8MB de tamaño; de acuerdo a cada escenario de prueba.
* El archivo plantilla en Jmeter se encuentra en el repositorio en el archivo: [HTTP_Request_cargar_videos.jmx](HTTP_Request_cargar_videos.jmx)
* Los archivos con los resultados de las pruebas se encuentran en la carpeta [/results](results/).
* Al realizar la prueba de escalamiento rápido, se encontró que la capa web soporta hasta 100 usuarios concurrentes en un periodo de tiempo de 3 minutos sin presentar degradación. El 97% de las peticiones presentaron respuesta exitosa y una latencia menor a los 1000ms.
* A partir de 150 usuarios, se empiezan a observar errores 500 en las respuestas, y la latencia de las peticiones empieza a aumentar hasta llegar a un punto máximo de 30 segundos.
* A partir de esto se determina que el valor de RPS (Request per second) es de aproximadamente 0.6.
* A partir de los logs del aplicativo, se encontró que el cuello de botella es la base de datos. Se está alcanzando el límite de conexiones rapidamente, lo que tumba la conexión entre el aplicativo y la base de datos, dejando el sistema inutilizable hasta que este se reinicie.
* A continuación se presentan los gráficos de la ejecución de la prueba.

### 100 usuarios
** Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1307" height="735" alt="image" src="https://github.com/user-attachments/assets/249573f0-f7ba-4057-9fee-850fd4500838" />
** Latencia
<img width="1287" height="567" alt="image" src="https://github.com/user-attachments/assets/cec448b9-248c-4a9c-b38e-d8b1791823da" />

### 150 usuarios
** Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1306" height="735" alt="image" src="https://github.com/user-attachments/assets/462e1b95-bbc4-423d-96d1-e20678d284dc" />

** Latencia
<img width="1286" height="567" alt="image" src="https://github.com/user-attachments/assets/9aae1ddd-0783-40d6-b140-3d1cc8e0014a" />

### 200 usuarios
** Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1307" height="735" alt="image" src="https://github.com/user-attachments/assets/84a112d9-b454-4def-8b21-c2def0f3713e" />

** Latencia
<img width="1287" height="567" alt="image" src="https://github.com/user-attachments/assets/0c5d4079-7d5b-4539-ad59-a69d932bb9d8" />

## Recomendaciones para escalar la solución
* Aumentar la capacidad del contenedor donde se aloja la base de datos, para aumentar el tiempo de procesamiento de cada solucitud y aumentar la disponibilidad del pool de conexiones.
* Utilizar una solución de caché en busquedas recurrentes, como el caso de la obtención de los usuarios a partir del token de autenticación.
