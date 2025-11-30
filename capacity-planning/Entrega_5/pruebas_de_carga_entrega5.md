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
* Al realizar la prueba de escalamiento rápido, se encontró que la capa web soporta hasta 47 usuarios concurrentes en un periodo de tiempo de 3 minutos presentando una degradación nula. El 58% de las peticiones presentaron respuesta exitosa, mientras que la latencia se mantuvo en valores al rededor de los 2000ms hasta que el sistema falló y empezó a dar timeout de aproximadamente 30 segundos.
* A partir de 120 usuarios, aproximadamente en el 31% fueron exitosas, lo cual representa una degradación importante, en este caso la latencia incrementó notablemente llegando a ser de hasta 15000ms en respuestas exitosas.
* A partir de esto se determina que el valor de RPS (Request per second) es de aproximadamente 0.261, lo que representó una degradación significativa con respecto al RPS de la entrega anterior (0.611).
* A partir de los logs del aplicativo, se encontró que el cuello de botella es la base de datos. Se está alcanzando el límite de conexiones rapidamente, lo que tumba la conexión entre el aplicativo y la base de datos, dejando el sistema inutilizable hasta que este se reinicie. Adicionalmente se observó que la cola de mensajes almacenaba una cantidad considerable de estos, lo que saturaba los workers.
* A continuación se presentan los gráficos de la ejecución de la prueba.

#### 80 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1055" height="618" alt="image" src="https://github.com/user-attachments/assets/3494fb0c-e4b4-47e3-b2c6-bed3b781f872" />

* Latencia
<img width="1045" height="444" alt="image" src="https://github.com/user-attachments/assets/4ecf6845-1b75-480b-8a25-e7ebc34279da" />

#### 120 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1053" height="610" alt="image" src="https://github.com/user-attachments/assets/602ef43d-13a8-4466-915d-25b70e0050f2" />

* Latencia
<img width="1047" height="449" alt="image" src="https://github.com/user-attachments/assets/6880aea3-6dbc-4ed8-9f64-f27e56bb1002" />

#### 150 usuarios
* Peticiones exitosas (verde) y peticiones fallidas (rojo)
<img width="1058" height="616" alt="image" src="https://github.com/user-attachments/assets/dabcba8b-a631-4cdf-804d-1852a9001ef2" />

* Latencia
<img width="1047" height="457" alt="image" src="https://github.com/user-attachments/assets/503ea718-67ab-4b9c-bba4-f649c60adc8e" />



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
 ### Uso de CPU en las pruebas de carga para 50 MB en la instancia inicial: 
 <img width="1595" height="680" alt="instancia 2" src="https://github.com/user-attachments/assets/01f03905-fdca-41c2-8b83-2173b81cdc9d" />


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

 ### Uso de CPU en las pruebas de carga para 100 MB en una de las instancias de autoescalado. 
 <img width="1681" height="690" alt="Instancia 1" src="https://github.com/user-attachments/assets/6785fb63-eb42-43cd-8f40-f510d4aec0b9" />

 ### Replicación de las instancias Worker, se evidencia la instancia original y las dos instancias replicadas.
<img width="1264" height="302" alt="Replicación de instancias worker" src="https://github.com/user-attachments/assets/484b227f-e5de-4839-98c6-ff9391ad7796" />

 
|Tamaño Video| Parametros               | Videos/minuto | Uso Promedio CPU |
|------------|--------------------------|---------------|------------------|
|50 MB       | 1 video cada 30 segundos a la cola| 0.96          | 73%-75%          |
|50 MB       | 1 video cada 60 segundos a la cola | 0.96          | 72%-74%          |
|100 MB      | 1 video cada 30 segundos a la cola | 0.57          | 80%-83%          |
|100 MB      | 1 video cada 60 segundos a la cola | 0.58          | 82%-84%          |
### Recomendaciones para escalar la solución
* Aumentar el número de máquinas virtuales worker para distribuir la carga de procesamiento en varios servidores y mitigar el cuello de botella de la CPU. 
Para videos de 50MB se tuvo que la cantidad de instancias fue suficiente para mantener un valor constante de videos en la cola SQS sin saturarse, sin embargo para videos de 100MB, la cantidad de instancias no fue suficiente.
