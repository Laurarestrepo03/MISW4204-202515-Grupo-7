# Arquitectura Entrega 4 del Sistema - ANB

## Descripción General
El sistema ANB es una plataforma de gestión y votación de videos de baloncesto desplegada en AWS. En esta cuarta entrega, la arquitectura evoluciona para incorporar **procesamiento asíncrono mediante AWS SQS** (Amazon Simple Queue Service) en lugar de Celery/Redis, y añade **Auto Scaling automático para los workers** que procesan videos, garantizando mayor escalabilidad y desacoplamiento del sistema.

### Características Principales

- API REST con FastAPI (con auto escalado horizontal)
- Balanceador de carga (Elastic Load Balancer) para el backend
- Auto Scaling Group para backend REST
- **🆕 Procesamiento asíncrono de videos con AWS SQS (reemplaza Celery/Redis)**
- **🆕 Auto Scaling Group para workers de procesamiento**
- **🆕 Balanceador de carga para workers (health checks)**
- Almacenamiento en S3 para videos originales y procesados
- Base de datos PostgreSQL en RDS
- Arquitectura completamente desacoplada y escalable

---

## Cambios Arquitectónicos Respecto a la Entrega 3

### 🆕 Nuevos Componentes

#### AWS SQS (Simple Queue Service)

- **Cola de mensajes**: `ANB_SQS`
- **Función**: Intermediario entre el backend REST y los workers
- **Tipo de mensajes**: Contienen el `video_id` del video a procesar
- **Ventajas sobre Celery/Redis**:
  - Servicio gestionado por AWS (sin servidor Redis que mantener)
  - Escalabilidad automática ilimitada
  - Persistencia garantizada de mensajes
  - No requiere infraestructura adicional
  - Menor costo operacional

#### Auto Scaling Group para Workers

- **Nombre**: `worker-asg`
- **Función**: Crear y destruir instancias worker automáticamente según la carga de CPU
- **Configuración**:
  - Capacidad mínima: 1 instancia
  - Capacidad deseada: 1-2 instancias
  - Capacidad máxima: 3 instancias
- **Política de Escalado**: Target Tracking al 50% de utilización de CPU
  - **Scale Out**: Cuando CPU promedio > 50%
  - **Scale In**: Cuando CPU promedio < 50%

#### Load Balancer para Workers (Health Checks)

- **Función**: Realizar health checks a las instancias worker
- **Puerto de health check**: 80 (endpoint HTTP simple)
- **Objetivo**: Permitir que el Auto Scaling Group detecte instancias unhealthy y las reemplace

### 🔄 Componentes Modificados

#### Workers de Procesamiento

- **Antes (Entrega 3)**: Una única instancia EC2 con Celery Worker
- **Ahora (Entrega 4)**: Múltiples instancias (1-3) con **SQS Worker**
- **Cambios clave**:
  - **Eliminado**: Celery, Redis, polling periódico de base de datos
  - **Agregado**: Cliente SQS de AWS 
  - **Mecanismo**: Los workers escuchan la cola SQS constantemente (long polling)
  - **Procesamiento**: Cada worker consume mensajes de la cola, procesa el video, y elimina el mensaje al terminar
- **Dockerizado**: Ejecutan en contenedores Docker con variables de entorno

#### Backend REST

- **Cambio**: Cuando se sube un video, el backend envía un mensaje a **SQS** con el `video_id` (en lugar de marcar en la BD y esperar polling)
- **Ventaja**: Comunicación asíncrona inmediata sin necesidad de polling

### ❌ Componentes Eliminados

- **Redis**: Ya no se usa como broker de mensajes
- **Celery**: Reemplazado completamente por SQS Worker
- **Polling de Base de Datos**: Los workers ya no revisan la BD cada minuto buscando videos pendientes

---

## Arquitectura de Despliegue en AWS (Entrega 4)

La arquitectura ahora se compone de 9 componentes principales:

### 1️⃣ Load Balancer Backend - ELB

- **Función**: Punto de entrada único para el backend REST
- **Configuración**: (sin cambios respecto a Entrega 3)
- **Target Group**: `backend-rest-target-group`

### 2️⃣ Auto Scaling Group Backend

- **Nombre**: `backend-rest-asg`
- **Configuración**: (sin cambios respecto a Entrega 3)
- **Política de Escalado**: Target Tracking al 50% CPU

### 3️⃣ Instancias EC2 - Backend REST

- **Cantidad**: 1-3 instancias (dinámico)
- **Cambio principal**: Al subir un video, envía un mensaje a **SQS** con el `video_id`


### 4️⃣ AWS SQS - Cola de Mensajes

- **Nombre de la cola**: `ANB_SQS`
- **Función**: Almacenar mensajes con IDs de videos pendientes de procesamiento
- **Tipo**: Cola estándar (FIFO no necesaria para este caso)
- **Configuración**:
  - **Retention period**: 4 días (tiempo máximo que un mensaje permanece en la cola)
  - **Visibility timeout**: 5 minutos (tiempo que un mensaje está "invisible" después de ser leído por un worker)
  - **Message format**:
    ```json
    {
      "video_id": 123
    }
    ```
- **Acceso**:
  - **Backend REST**: Escritura (envío de mensajes)
  - **Workers**: Lectura y eliminación de mensajes
- **Ventajas**:
  - Desacoplamiento total entre backend y workers
  - Persistencia automática de mensajes
  - No se pierden trabajos si los workers están caídos
  - Escalabilidad ilimitada

### 5️⃣ Load Balancer Workers - ELB (Health Checks)

- **Tipo**: Application Load Balancer
- **Función**: Realizar health checks a las instancias worker
- **Puerto**: 80 (endpoint HTTP simple que devuelve `200 OK`)
- **Health Check Configuration**:
  - Path: `/` o `/health`
  - Intervalo: 30 segundos
  - Timeout: 5 segundos
  - Unhealthy threshold: 2 checks fallidos
- **Objetivo**: Permitir que el ASG detecte workers que no responden y los reemplace

### 6️⃣ Auto Scaling Group Workers

- **Nombre**: `worker-asg`
- **Función**: Crear y destruir instancias worker según la utilización de CPU
- **Configuración**:
  - Capacidad mínima: 1 instancia
  - Capacidad deseada: 1-2 instancias
  - Capacidad máxima: 3 instancias
  - Launch Template: `worker-launch-template`
  - Zonas de disponibilidad: us-east-1a, us-east-1b

- **Política de Escalado (Target Tracking)**:
  
  **Tipo**: Target Tracking Scaling Policy
  
  **Métrica objetivo**: Utilización promedio de CPU al 50%
  
  **Funcionamiento**: AWS ajusta automáticamente la cantidad de instancias worker para mantener el CPU promedio en 50%
  
  **Scale Out (Agregar Workers)**:
  - **Trigger**: Cuando el CPU promedio supera el 50% de forma sostenida
  - **Proceso**:
    1. CloudWatch monitorea la utilización de CPU de los workers activos
    2. Cuando el promedio supera el 50%, se notifica al ASG
    3. El ASG crea una nueva instancia worker usando el Launch Template
    4. El User Data script se ejecuta automáticamente
    5. **Warmup Period (300 segundos)**: La nueva instancia procesa videos pero su CPU no se incluye en las métricas del ASG
    6. Después del warmup, la instancia pasa los health checks del Load Balancer
    7. La nueva instancia comienza a consumir mensajes de SQS
    8. La carga se distribuye entre más workers, reduciendo el CPU promedio hacia el 50%
  - **Razón**: Cuando el procesamiento de videos es intensivo (CPU alto), se necesitan más workers para mantener el rendimiento
  
  **Scale In (Quitar Workers)**:
  - **Trigger**: Cuando el CPU promedio cae por debajo del 50% de forma sostenida
  - **Proceso**:
    1. CloudWatch detecta que el CPU promedio está consistentemente bajo
    2. El ASG determina que hay capacidad de sobra
    3. Se selecciona una instancia para terminar
    4. El worker termina de procesar el mensaje actual (si tiene alguno)
    5. La instancia se termina una vez que no hay trabajo en curso
    6. El Load Balancer actualiza su lista de instancias disponibles
  - **Razón**: Optimizar costos eliminando capacidad innecesaria cuando no hay videos que procesar o la carga es baja
  
  **Ventajas de esta métrica**:
  - El procesamiento de videos con FFmpeg es intensivo en CPU
  - Un solo video puede saturar el CPU de una instancia t3.micro
  - Escalar por CPU garantiza que siempre haya capacidad para procesar videos rápidamente
  - Cuando la cola SQS está vacía, el CPU baja naturalmente y se reducen instancias automáticamente

  **Warmup Period**: 300 segundos (tiempo que una nueva instancia necesita antes de ser incluida en las métricas de CPU del ASG)

### 7️⃣ Instancias EC2 - SQS Workers

- **Cantidad**: 1-3 instancias (dinámico, gestionado por ASG)
- **Tipo de instancia**: t3.small
- **Servicio**: SQS Worker 
- **Función**: Procesar videos de manera asíncrona
- **Responsabilidades** (cada worker):
  - Escuchar constantemente la cola SQS (long polling de 20 segundos)
  - Consumir mensajes con `video_id`
  - Descargar video original desde S3
  - Procesar video (conversión + marca de agua con FFmpeg)
  - Subir video procesado a S3
  - Actualizar estado en PostgreSQL (`status = 'PROCESSED'`)
  - Eliminar mensaje de SQS al completar exitosamente


- **Despliegue Automático**:
  - User Data script ejecutado al crear cada instancia
  - Instala Docker y Docker Compose
  - Clona el repositorio desde GitHub
  - Crea archivo `.env` con variables de entorno (incluyendo `SQS_URL`)
  - Levanta contenedor worker con `docker run -d`

- **Puerto Expuesto**: 80 (para health checks del Load Balancer)

- **Características Importantes**:
  - **Stateless**: No mantienen estado entre ejecuciones
  - **Idénticos**: Todos ejecutan el mismo código
  - **Efímeros**: Pueden ser creados o destruidos en cualquier momento
  - **Concurrentes**: Múltiples workers pueden procesar videos simultáneamente sin conflictos
  - **Tolerantes a fallos**: Si un worker falla, el mensaje vuelve a la cola y otro worker lo procesa

### 8️⃣ Instancia RDS - Base de Datos PostgreSQL

- **Sin cambios** respecto a Entrega 3
- **Eliminado**: La columna `task_id` de Celery ya no se usa 

### 9️⃣ S3 Bucket - Almacenamiento de Videos

- **Sin cambios** respecto a Entrega 3
- **Estructura**:
  - `original_videos/`: Videos subidos por usuarios
  - `processed_videos/`: Videos procesados con marca de agua

---

## Diagramas

### Diagrama de Componentes (Entrega 4)

![Diagrama de Componentes](url-del-diagrama-de-componentes)

El diagrama muestra:

- Cliente HTTP conectado al Load Balancer Backend
- Load Balancer Backend conectado al Target Group del Backend REST
- Target Group Backend conteniendo múltiples instancias Backend REST
- Instancias Backend REST comunicándose con:
  - Base de datos RDS PostgreSQL
  - Bucket S3
  - **🆕 Cola SQS** (envío de mensajes)
- **🆕 Cola SQS** como componente independiente
- **🆕 Worker Instance Pool** conteniendo múltiples instancias worker
- Workers escuchando la cola SQS (polling)
- Workers comunicándose con:
  - Base de datos RDS PostgreSQL (actualización de estado)
  - Bucket S3 (lectura de originales, escritura de procesados)
- **🆕 Load Balancer Workers** para health checks

### Diagrama de Despliegue (Entrega 4)

![Diagrama de Despliegue](url-del-diagrama-de-despliegue)

El diagrama de despliegue ilustra:

**Subred Pública AZ2 (us-east-1a)**:
- Load Balancer Backend + ASG Backend
- Instancias EC2 Backend (Ubuntu 24.04) con ANB-App

**Subred Pública AZ1 (us-east-1b)**:
- Instancias EC2 Backend adicionales
- **🆕 SQS** (cola asíncrona)
- **🆕 Load Balancer Workers + ASG Workers**
- **🆕 Instancias EC2 Workers** (Ubuntu 24.04) con ProcesadorVideos
- AWS-RDS (PostgreSQL)
- AWS-S3 (almacenamiento)

---

## Flujo de Peticiones y Procesamiento (Entrega 4)

### 📱 Fase 1: Usuario sube un video

1. Cliente envía `POST /api/videos/upload` al DNS del Load Balancer Backend
2. Load Balancer distribuye la petición a una instancia Backend REST
3. Instancia Backend:
   - Valida el token JWT
   - Sube el video a S3 (`original_videos/`)
   - Crea registro en PostgreSQL con `status = 'UPLOADED'`
   - **🆕 Envía mensaje a SQS** con el `video_id`
   - Devuelve respuesta al cliente: `{"message": "Video subido correctamente. Procesamiento en curso", "video_id": 123}`

### ⚙️ Fase 2: Worker procesa el video

1. **Uno de los workers** (puede ser cualquiera) recibe el mensaje de SQS mediante long polling
2. Worker extrae el `video_id` del mensaje
3. Worker descarga el video original desde S3
4. Worker procesa el video:
   - Conversión de formato
   - Añade marca de agua con FFmpeg
5. Worker sube el video procesado a S3 (`processed_videos/`)
6. Worker actualiza el registro en PostgreSQL:
   - `status = 'PROCESSED'`
   - `processed_url`: URL del S3
7. **Worker elimina el mensaje de SQS** (confirmación de procesamiento exitoso)

**Ventaja clave**: Si el worker falla antes de eliminar el mensaje, el mensaje vuelve a estar visible después del "visibility timeout" y otro worker puede procesarlo.

### 🔄 Fase 3: Auto Scaling de Workers

**Escenario 1: Muchos videos subidos simultáneamente**
1. Se acumulan 10 mensajes en la cola SQS
2. Múltiples workers comienzan a procesar videos en paralelo
3. El CPU de los workers sube a 80-90% (FFmpeg es intensivo)
4. CloudWatch detecta CPU promedio > 50% sostenido
5. Auto Scaling Group crea una nueva instancia worker
6. La nueva instancia comienza a consumir mensajes de SQS
7. La carga se distribuye entre más workers
8. Los videos se procesan en paralelo más rápidamente

**Escenario 2: No hay videos pendientes**
1. Cola SQS vacía → Workers en idle
2. CPU promedio: ~5-10% (solo escuchando SQS)
3. CloudWatch detecta CPU promedio < 50% sostenido
4. Auto Scaling Group reduce la capacidad en -1
5. Una instancia worker se termina (después de completar su trabajo actual)
6. **Resultado**: Solo 1 worker en idle, optimizando costos

---

## Mecanismo de Auto Escalado de Workers

### 📊 Métrica de Escalado: Utilización de CPU

Los workers escalan según la **utilización promedio de CPU**, que refleja directamente la carga de procesamiento de videos.

**¿Por qué CPU y no mensajes en SQS?**

Se utiliza escalado segun uso de CPU porque:

1. **FFmpeg es intensivo en CPU**: El procesamiento de videos (conversión + marca de agua) consume mucho CPU
2. **Un solo video puede saturar una instancia**: Una instancia t3.micro puede llegar al 80-90% CPU procesando un solo video
3. **Refleja mejor la necesidad real**: Si el CPU está alto, significa que los workers están sobrecargados independientemente de cuántos mensajes hay en la cola
4. **Auto-regulación natural**: Cuando no hay mensajes, el worker está en "idle" (CPU ~5%), lo que naturalmente dispara el scale-in

**Configuración de Target Tracking:**

- **Tipo de política**: Target Tracking Scaling
- **Métrica objetivo**: `CPUUtilization` (AWS/EC2)
- **Valor objetivo**: 50%
- **Warmup period**: 300 segundos

**Proceso de escalado:**

**Cuando CPU promedio > 50%**:
1. AWS evalúa las métricas cada 60 segundos
2. Detecta una tendencia sostenida de CPU alto
3. Crea una nueva instancia worker
4. La nueva instancia comienza a consumir mensajes de SQS
5. La carga se distribuye, reduciendo el CPU promedio

**Cuando CPU promedio < 50%**:
1. AWS detecta CPU bajo de forma sostenida
2. Determina que hay capacidad de sobra
3. Termina una instancia worker (después de completar su trabajo actual)
4. Optimiza costos manteniendo solo la capacidad necesaria

### 🔍 Ejemplo Práctico

**Escenario**: Se suben 5 videos simultáneamente

1. **t=0**: Hay 1 worker procesando 1 video → CPU al 85%
2. **t=60s**: CloudWatch detecta CPU > 50% sostenido
3. **t=120s**: Se crea Worker 2 (warmup de 300s)
4. **t=420s**: Worker 2 termina warmup, comienza a procesar
5. **Resultado**: 
   - Worker 1: procesando video → CPU 85%
   - Worker 2: procesando video → CPU 85%
   - **CPU promedio: 85%** → Sigue siendo alto
6. **t=480s**: Se crea Worker 3
7. **Distribución final**: 3 workers procesando 5 videos
   - CPU promedio: ~55-60%
   - Todos los videos se procesan en paralelo

**Cuando terminan de procesar**:
1. Cola SQS vacía → Workers en idle
2. CPU promedio: ~5-10% (solo escuchando SQS)
3. CloudWatch detecta CPU < 50% sostenido
4. ASG reduce a 1 instancia después de varios minutos
5. **Resultado**: Solo 1 worker en idle, optimizando costos

### 🏥 Health Checks del Load Balancer

El Load Balancer para workers realiza health checks para detectar instancias no saludables:

- **Puerto**: 80
- **Path**: `/` o `/health`
- **Intervalo**: 30 segundos
- **Unhealthy threshold**: 2 checks fallidos consecutivos

**Si un worker falla**:
1. Deja de responder al health check
2. El Load Balancer marca la instancia como "unhealthy"
3. El ASG detecta la instancia unhealthy
4. El ASG termina la instancia y crea una nueva
5. El mensaje que estaba procesando vuelve a SQS (después del visibility timeout)
6. Otro worker procesa el video

---

## Ventajas de la Nueva Arquitectura (Entrega 4)

### ✅ Comparado con Celery/Redis (Entrega 3)

| Aspecto | Celery/Redis (Entrega 3) | SQS (Entrega 4) |
|---------|--------------------------|-----------------|
| **Infraestructura** | Requiere servidor Redis | Servicio gestionado por AWS |
| **Mantenimiento** | Mantener Redis funcionando | Cero mantenimiento |
| **Escalabilidad** | Limitada por capacidad de Redis | Ilimitada |
| **Persistencia** | Depende de configuración de Redis | Garantizada por AWS (4 días) |
| **Costo** | Instancia EC2 para Redis | Solo pago por uso (muy económico) |
| **Resiliencia** | Si Redis cae, se pierden trabajos | Mensajes persisten incluso si workers caen |

### ✅ Auto Scaling Inteligente de Workers

- Los workers escalan según la **carga real de trabajo** (utilización de CPU)
- No se desperdician recursos cuando no hay videos que procesar
- Procesamiento paralelo automático en picos de demanda
- Balance óptimo entre rendimiento y costo

### ✅ Escalado Basado en Carga Real

- Los workers escalan según la **intensidad del procesamiento** (CPU), no solo por cantidad de videos
- Un video de 4K que requiere mucho procesamiento disparará el escalado apropiadamente
- Múltiples videos ligeros pueden procesarse con menos workers
- Balance óptimo entre rendimiento y costo

### ✅ Desacoplamiento Total

- Backend y Workers no se comunican directamente
- Backend no necesita saber cuántos workers hay
- Workers pueden fallar sin afectar al backend
- Se pueden escalar backend y workers independientemente

### ✅ Tolerancia a Fallos

- Si un worker falla mientras procesa, el mensaje vuelve a la cola
- Otro worker puede retomar el trabajo automáticamente
- No se pierden trabajos pendientes

---

## Comparación: Entrega 3 vs Entrega 4

| Aspecto | Entrega 3 | Entrega 4 |
|---------|-----------|-----------|
| **Comunicación Backend-Worker** | Polling de BD cada 1 min | Mensajes en SQS (inmediato) |
| **Broker de Mensajes** | Celery + Redis | AWS SQS |
| **Worker** | 1 instancia fija con Celery | 1-3 instancias con SQS Worker |
| **Auto Scaling Workers** | No | Sí (basado en CPU) |
| **Política de Escalado Workers** | N/A (1 instancia fija) | Target Tracking al 50% CPU |
| **Infraestructura adicional** | Redis en EC2 | Solo SQS (gestionado) |
| **Persistencia de trabajos** | Depende de Redis | Garantizada por SQS |
| **Desacoplamiento** | Parcial (BD compartida) | Total (mensajería asíncrona) |
| **Health Checks Workers** | No | Sí (Load Balancer) |

---

## Conclusión

La arquitectura de la Entrega 4 representa la evolución hacia un sistema de **microservicios completamente desacoplado y escalable**. La adopción de **AWS SQS** elimina la necesidad de mantener infraestructura adicional (Redis) y proporciona una solución más robusta, escalable y tolerante a fallos para el procesamiento asíncrono de videos.

El **Auto Scaling automático de workers** basado en la utilización de CPU garantiza que el sistema siempre tenga la capacidad necesaria para procesar videos de manera eficiente, escalando dinámicamente según la intensidad del procesamiento requerido, sin desperdiciar recursos durante periodos de baja demanda.

Esta arquitectura está lista para entornos de producción con alta carga y requisitos estrictos de disponibilidad y escalabilidad.

---

**Documentación actualizada**: 16 de noviembre de 2025  
**Versión**: 4.0 (AWS con SQS Worker y Auto Scaling de Workers basado en CPU)