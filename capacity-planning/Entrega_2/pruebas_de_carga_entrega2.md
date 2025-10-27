# Análisis de capacidad

## Escenarios de prueba planteados:

### Escenario 1 - Capacidad de la capa Web (usuarios concurrentes)
Determinar el número de usuarios concurrentes que la API de subida soporta cumpliendo SLOs, sin estar limitado por la capa asíncrona.

### Estrategia de implementación
Se desacopló la capa de procesamiento asíncrono para la realización de estas pruebas. Para esto simplemente se desactivo el servicio ejecutandose en el servidor del worker.
De esta forma, la capa Web no se ve limitada por la capacidad de procesamiento de los videos.

### Escenarios de prueba
* **Escalamiento rápido (Ramp):** iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 80 → 120 → 150) hasta observar degradación.

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
(Modificar)
* Se crearon 3 treads de usuarios en JMeter, cada uno enviando peticiones de subida de video de aproximadamente 8MB de tamaño; de acuerdo a cada escenario de prueba.
* El archivo plantilla en Jmeter se encuentra en el repositorio en el archivo: [HTTP_Request_cargar_videos.jmx](HTTP_Request_cargar_videos.jmx)
* Los archivos con los resultados de las pruebas se encuentran en la carpeta [/results](results/).
* Al realizar la prueba de escalamiento rápido, se encontró que la capa web soporta hasta 80 usuarios concurrentes en un periodo de tiempo de 3 minutos sin presentar una degradación significativa. El 90% de las peticiones presentaron respuesta exitosa, aunque la latencia alcanzó niveles significativos, llegando a varios segundos en algunas peticiones.
* A partir de 120 usuarios, se empiezan a observar una mayor cantidad de errores 500 en las respuestas, aproximadamente en el 17%, y la latencia de las peticiones empieza a aumentar hasta llegar a un valores por encima de los 100 segundos.
* A partir de esto se determina que el valor de RPS (Request per second) es de aproximadamente 0.44.
* A partir de los logs del aplicativo, se encontró que el cuello de botella es la base de datos. Se está alcanzando el límite de conexiones rapidamente, lo que tumba la conexión entre el aplicativo y la base de datos, dejando el sistema inutilizable hasta que este se reinicie.
* A continuación se presentan los gráficos de la ejecución de la prueba.

### 80 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
(Colocar imagenes)

* Latencia
(Colocar imagenes)

### 120 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
(Colocar imagenes)

* Latencia
(Colocar imagenes)

### 150 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
(Colocar imagenes)

* Latencia
(Colocar imagenes)

## Recomendaciones para escalar la solución
* Se recomienda 

### Escenario 2 - Capacidad de la capa Web (usuarios concurrentes)
Medir cuántos videos por minuto procesa el worker a distinto volúmen de videos a ejecutar.

### Diseño experimental
Tamaño de video: 30 MB aproximadamente. Enviar lotes de un video cada 30 segundos - 1 minuto. Realizar esto 10 veces.

### Métricas y cálculos
* X = videos procesados por / minuto
* S = tiempo_proceso_promedio por video.

### Criterios de éxito/fallo
Capacidad nominal: (videos/min)

### Herramientas utilizadas
* Generador de eventos: Script en Python para inyectar directamente en la base de datos videos a procesar.
* Perfilado del worker: Htop

### Salidas esperadas
* Capacidad por tamaño y configuración (1 nodos × 4 hilos → 18.5 videos/min a 200
MB).
* Puntos de saturación y cuellos de botella (CPU, decodificación, ancho de banda, temp disk).

## Resultados

Se ejecutó el Script en python para la ejecución del worker, inyectando videos en la base de datos directamente. Esto hace que el worker busque los videos sin procesar y los procese de forma secuencial.

Finalmente se reviso en la base de datos el tiempo estimado en procesar cada video y el tiempo en procesar todos los videos.
Adicionalmente mediante la herramienta htop se monitoreo el uso de CPU y memoria del worker durante la ejecución.

* Inyección de 1 video (30MB) cada 30 segundos:
  - Videos procesados: 10
  - Tiempo total de procesamiento: 18 minutos
  - Tiempo promedio por video: 1.8 minutos
  - Uso promedio de CPU: 89%
  - Uso promedio de memoria: 820MB
  - Videos procesados por minuto: 1 nodo x 1 hilo -> 0.55 videos/minuto a 30MB
  - Puntos de saturación: CPU al 95% al terminar de enviarse todos los videos.
* Inyección de 1 video (30MB) cada 60 segundos:
  - Videos procesados: 10
  - Tiempo total de procesamiento: 16 minutos
  - Tiempo promedio por video: 1.6 minutos
  - Uso promedio de CPU: 90%
  - Uso promedio de memoria: 810MB
  - Videos procesados por minuto: 1 nodo x 1 hilo -> 0.625 videos/minuto a 30MB
  - Puntos de saturación: CPU al 96% al terminar de enviarse todos los videos.
 
    <img width="1344" height="704" alt="HTOP" src="https://github.com/user-attachments/assets/e77d9bba-a4e7-4a4a-91f4-0ef308553086" />

## Recomendaciones para escalar la solución
* Aumentar el número de hilos del worker para aprovechar mejor la capacidad de la CPU.
* Aumentar el número de máquinas virtuales worker para distribuir la carga de procesamiento en varios servidores y mitigar el cuello de botella de la CPU.
