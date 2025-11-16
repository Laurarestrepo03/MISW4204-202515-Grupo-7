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
* Observabilidad: Excel

### Salidas esperadas
* Curva usuarios→latencia/errores/exitos.
* RPS sostenido a capacidad máxima.
* Bottlenecks con evidencias.

### Resultados
* Se crearon 3 treads de usuarios en JMeter, cada uno enviando peticiones de subida de video de aproximadamente 8MB de tamaño; de acuerdo a cada escenario de prueba.
* El archivo plantilla en Jmeter se encuentra en el repositorio en el archivo: [HTTP_Request_cargar_videos.jmx](HTTP_Request_cargar_videos.jmx)
* Los archivos con los resultados de las pruebas se encuentran en la carpeta [/results](results/).
* Al realizar la prueba de escalamiento rápido, se encontró que la capa web soporta hasta 80 usuarios concurrentes en un periodo de tiempo de 3 minutos presentando una degradación considerable. El 78% de las peticiones presentaron respuesta exitosa, mientras que la latencia se mantuvo en niveles intermedios, llegando a varios segundos en algunas peticiones.
* A partir de 120 usuarios, se empiezan a observar una mayor cantidad de errores 500 en las respuestas, aproximadamente en el 51%, y la latencia de las peticiones empieza a aumentar hasta llegar a un valores por encima de los 30 segundos.
* A partir de esto se determina que el valor de RPS (Request per second) es de aproximadamente 0.34.
* A partir de los logs del aplicativo, se encontró que el cuello de botella es la base de datos. Se está alcanzando el límite de conexiones rapidamente, lo que tumba la conexión entre el aplicativo y la base de datos, dejando el sistema inutilizable hasta que este se reinicie.
* A continuación se presentan los gráficos de la ejecución de la prueba.

#### 80 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1144" height="666" alt="image" src="https://github.com/user-attachments/assets/62bbd710-8387-4708-bddd-6a57740f401e" />


* Latencia
<img width="1135" height="476" alt="image" src="https://github.com/user-attachments/assets/860a8522-d90d-46c5-9baf-2f9f41a9531a" />



#### 120 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1055" height="613" alt="image" src="https://github.com/user-attachments/assets/17286c86-93a7-4d12-8dea-872cafbc7e53" />


* Latencia
<img width="1040" height="463" alt="image" src="https://github.com/user-attachments/assets/94ca9703-61d4-4bbf-b033-e55f8ac00b04" />



#### 150 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1055" height="625" alt="image" src="https://github.com/user-attachments/assets/43b0fb20-94d9-4a3b-b3f0-a5e725f4f4de" />



* Latencia
<img width="1041" height="454" alt="image" src="https://github.com/user-attachments/assets/6bb61117-4510-4222-9ba1-b91ea3e61e60" />



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
* Generador de eventos: Script en Python para inyectar videos en cada una de las combinaciones presentadas anteriormente. La inyección de los videos se realizará automáticamente en la cola de mensajería SQS.
* Perfilado del worker: Monitoreo de CPU mediante cloudwatch en EC2. Monitoreo del tiempo de procesamiento de los videos mediante la base de datos.

### Salidas esperadas
* Capacidad por tamaño y configuración (4 nodos × 4 hilos → 18.5 videos/min a 200
MB).
* Puntos de saturación y cuellos de botella (CPU, decodificación).

### Resultados

Se ejecutó el Script en python para la ejecución del worker, inyectando videos directamente en la cola SQS. Esto hace que los videos sin procesar sean tomados por las máquinas worker disponibles de forma equitativa. El número de máquinas disponibles depende de las reglas establecidas en el grupo de autoescalado.

Finalmente se reviso en la base de datos el tiempo estimado en procesar cada video y el tiempo en procesar todos los videos, así como las métricas en cloudwatch para el monitoreo de CPU del worker.

* Inyección de 1 video (50MB) cada 30 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 19 minutos
  - Tiempo promedio por video: 2:57 minutos
  - Uso promedio de CPU: 72%
  - Videos procesados por minuto: 3 nodos x 1 hilo -> 0.96 videos/minuto a 50MB
  - Puntos de saturación: CPU al 73%, no hubo puntos de fallo, aunque se saturó la cola de mensajes, el tiempo total de procesamiento fue mucho menor. Esto gracias a que el trabajo se distribuyó entre 3 instancias worker.
* Inyección de 1 video (50MB) cada 60 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 38 minutos
  - Tiempo promedio por video: 2:57 minutos
  - Uso promedio de CPU: 74%
  - Videos procesados por minuto: 3 nodos x 1 hilo -> 0.96 videos/minuto a 50MB
  - Puntos de saturación: CPU al 75%, no hubo puntos de fallo, NO se saturó la cola de mensajes. La cantidad de mensajes en la cola SQS se mantuvo constante, ya que el tiempo de procesamiento por cada video era casi igual al tiempo en que se generaban los mensajes.
 ### Uso de CPU en las pruebas de carga para 50 MB en sus dos tandas: 
  <img width="1444" height="680" alt="CPU1" src="https://github.com/user-attachments/assets/7280cba3-ac9d-4e7c-a13f-86d812301fde" />

* Inyección de 1 video (100MB) cada 30 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 38 minutos
  - Tiempo promedio por video: 5:32 minutos
  - Uso promedio de CPU: 81%
  - Videos procesados por minuto: 3 nodos x 1 hilo -> 0.57 videos/minuto a 100MB
  - Puntos de saturación: CPU al 80% en el pico mas alto de procesamiento. La cola de mensajes se saturó desde el inicio, ya que el tiempo de procesamiento por cada video era mucho mayor al tiempo en que se generaban los mensajes. Sin embargo fue posible finalizar la prueba exitosamente.
* Inyección de 1 video (100MB) cada 60 segundos:
  - Videos procesados: 20
  - Tiempo total de procesamiento: 37 minutos
  - Tiempo promedio por video: 5:31 minutos
  - Uso promedio de CPU: 83%
  - Videos procesados por minuto: 3 nodos x 1 hilo -> 0.58 videos/minuto a 100MB
  - Puntos de saturación: CPU al 80% en el pico mas alto de procesamiento. La cola de mensajes se mantuvo constante los primeros dos minutos, eventualmente esta se saturó, ya que el tiempo de procesamiento por cada video era mucho mayor al tiempo en que se generaban los mensajes. Sin embargo fue posible finalizar la prueba exitosamente.

 ### Uso de CPU en las pruebas de carga para 100 MB. Se evidencia una caida repentina en el uso de CPU, esto se da por la saturación de CPU y el crasheo del servicio:
  <img width="1805" height="878" alt="CPU2" src="https://github.com/user-attachments/assets/9a0ae5a8-98ff-408a-9e19-d7b033204099" />

 
|Tamaño Video| Parametros               | Videos/minuto | Uso Promedio CPU |
|------------|--------------------------|---------------|------------------|
|50 MB       | 1 video cada 30 segundos a la cola| 0.96          | 73%-75%          |
|50 MB       | 1 video cada 60 segundos a la cola | 0.96          | 72%-74%          |
|100 MB      | 1 video cada 30 segundos a la cola | 0.57          | 80%-83%          |
|100 MB      | 1 video cada 60 segundos a la cola | 0.58          | 82%-84%          |
### Recomendaciones para escalar la solución
* Aumentar el número de máquinas virtuales worker para distribuir la carga de procesamiento en varios servidores y mitigar el cuello de botella de la CPU. 
Para videos de 50MB se tuvo que la cantidad de instancias fue suficiente para mantener un valor constante de videos en la cola SQS sin saturarse, sin embargo para videos de 100MB, la cantidad de instancias no fue suficiente.
