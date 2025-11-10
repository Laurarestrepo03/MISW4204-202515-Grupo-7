# Análisis de capacidad

## Escenario 1 - Capacidad de la capa Web (usuarios concurrentes)
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

### Resultados
* Se crearon 3 treads de usuarios en JMeter, cada uno enviando peticiones de subida de video de aproximadamente 8MB de tamaño; de acuerdo a cada escenario de prueba.
* El archivo plantilla en Jmeter se encuentra en el repositorio en el archivo: [HTTP_Request_cargar_videos.jmx](HTTP_Request_cargar_videos.jmx)
* Los archivos con los resultados de las pruebas se encuentran en la carpeta [/results](results/).
* Al realizar la prueba de escalamiento rápido, se encontró que la capa web soporta hasta 80 usuarios concurrentes en un periodo de tiempo de 3 minutos presentando una degradación considerable. El 90% de las peticiones presentaron respuesta exitosa, aunque la latencia alcanzó niveles significativos, llegando a varios segundos en algunas peticiones.
* A partir de 120 usuarios, se empiezan a observar una mayor cantidad de errores 500 en las respuestas, aproximadamente en el 17%, y la latencia de las peticiones empieza a aumentar hasta llegar a un valores por encima de los 100 segundos.
* A partir de esto se determina que el valor de RPS (Request per second) es de aproximadamente 0.44.
* A partir de los logs del aplicativo, se encontró que el cuello de botella es la base de datos. Se está alcanzando el límite de conexiones rapidamente, lo que tumba la conexión entre el aplicativo y la base de datos, dejando el sistema inutilizable hasta que este se reinicie.
* A continuación se presentan los gráficos de la ejecución de la prueba.

#### 80 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1082" height="667" alt="image" src="https://github.com/user-attachments/assets/1b5221ae-32a8-4302-896e-2499665ee64b" />

* Latencia
<img width="1075" height="468" alt="image" src="https://github.com/user-attachments/assets/c913a4ed-520f-4631-a2cb-20bfd218c3b2" />


#### 120 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1063" height="619" alt="image" src="https://github.com/user-attachments/assets/b0ec67dc-700f-445d-9ef1-868a118dbbfe" />

* Latencia
<img width="1044" height="445" alt="image" src="https://github.com/user-attachments/assets/cbb1e0a7-cdd9-4c7a-b993-65d142375714" />


#### 150 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1054" height="621" alt="image" src="https://github.com/user-attachments/assets/467e093d-a412-4fef-ae8e-ba54a5258513" />


* Latencia
<img width="1042" height="456" alt="image" src="https://github.com/user-attachments/assets/ee44e066-ce92-4d5a-9478-008efcf2143b" />


### Recomendaciones para escalar la solución
Se recomienda incrementar la capacidad de conexiones persistentes a la base de datos, para disminuir el cuello de botella que se presenta en dicha conexión.

## Escenario 2 - Capacidad de la capa Web (usuarios concurrentes)
Medir cuántos videos por minuto procesa el worker a distinto volúmen de videos a ejecutar y tamaño de videos.

### Diseño experimental
Tamaño de video: 50 MB y 100 MB aproximadamente. Enviar lotes de un video cada 30 segundos - 1 minuto. Realizar esto 20 veces.
#### Para cada combinación:
* Ejecutar pruebas de saturación: subir la cantidad de tareas progresivamente en la cola
* Ejecutar pruebas sostenidas: mantener un numero fijo de archivos en la cola que no la sature
### Métricas y cálculos
* X = videos procesados por / minuto
* S = tiempo_proceso_promedio por video.

### Criterios de éxito/fallo
Capacidad nominal: (videos/min)

### Herramientas utilizadas
* Generador de eventos: Script en Python para inyectar videos en cada una de las combinaciones presentadas anteriormente.
* Perfilado del worker: Monitoreo de CPU mediante cloudwatch en EC2. Monitoreo del tiempo de procesamiento de los videos mediante la base de datos.

### Salidas esperadas
* Capacidad por tamaño y configuración (1 nodos × 4 hilos → 18.5 videos/min a 200
MB).
* Puntos de saturación y cuellos de botella (CPU, decodificación).

### Resultados

Se ejecutó el Script en python para la ejecución del worker, inyectando videos directamente en este. Esto hace que el worker busque los videos sin un task_id y los procese de forma secuencial para cada una de las combinaciones presentadas.

Finalmente se reviso en la base de datos el tiempo estimado en procesar cada video y el tiempo en procesar todos los videos, así como las métricas en cloudwatch para el monitoreo de CPU del worker.

* Inyección de 1 video (50MB) cada 30 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 60 minutos
  - Tiempo promedio por video: 2:56 minutos
  - Uso promedio de CPU: 73%
  - Videos procesados por minuto: 1 nodo x 1 hilo -> 0.32 videos/minuto a 50MB
  - Puntos de saturación: CPU al 73%, no hubo puntos de fallo, se saturó la cola de mensajes.
* Inyección de 1 video (50MB) cada 60 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 120 minutos
  - Tiempo promedio por video: 2:57 minutos
  - Uso promedio de CPU: 75%
  - Videos procesados por minuto: 1 nodo x 1 hilo -> 0.32 videos/minuto a 50MB
  - Puntos de saturación: CPU al 75%, no hubo puntos de fallo, se saturó la cola de mensajes.
 ### Uso de CPU en las pruebas de carga para 50 MB en sus dos tandas: 
  <img width="1444" height="680" alt="CPU1" src="https://github.com/user-attachments/assets/7280cba3-ac9d-4e7c-a13f-86d812301fde" />

* Inyección de 1 video (100MB) cada 30 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 32 minutos
  - Tiempo promedio por video: 5:30 minutos
  - Uso promedio de CPU: 80%
  - Videos procesados por minuto: 1 nodo x 1 hilo -> 0.19 videos/minuto a 100MB
  - Puntos de saturación: CPU al 80% en el pico mas alto de procesamiento. Se saturó la CPU a mitad de las pruebas, lo que produjo que estas se detuvieran.
* Inyección de 1 video (100MB) cada 60 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 30 minutos
  - Tiempo promedio por video: 5:31 minutos
  - Uso promedio de CPU: 83%
  - Videos procesados por minuto: 1 nodo x 1 hilo -> 0.19 videos/minuto a 100MB
  - Puntos de saturación: CPU al 80% en el pico mas alto de procesamiento. Se saturó la CPU al realizar 5 procesamientos de video, lo que produjo que estas se detuvieran.

 ### Uso de CPU en las pruebas de carga para 100 MB. Se evidencia una caida repentina en el uso de CPU, esto se da por la saturación de CPU y el crasheo del servicio:
  <img width="1805" height="878" alt="CPU2" src="https://github.com/user-attachments/assets/9a0ae5a8-98ff-408a-9e19-d7b033204099" />

 
|Tamaño Video| Parametros               | Videos/minuto | Uso Promedio CPU |
|------------|--------------------------|---------------|------------------|
|50 MB       | 1 video cada 30 segundos a la cola| 0.32          | 73%-75%          |
|50 MB       | 1 video cada 60 segundos a la cola | 0.32          | 73%-75%          |
|100 MB      | 1 video cada 30 segundos a la cola | 0.19          | 80%-83%          |
|100 MB      | 1 video cada 60 segundos a la cola | 0.19          | 80%-83%          |
### Recomendaciones para escalar la solución
* Aumentar el número de máquinas virtuales worker para distribuir la carga de procesamiento en varios servidores y mitigar el cuello de botella de la CPU.
