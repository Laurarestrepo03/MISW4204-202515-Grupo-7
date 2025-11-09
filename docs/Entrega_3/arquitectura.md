# Arquitectura Entrega 3 del Sistema - ANB Rising Stars

## Descripción General
El sistema ANB  es una plataforma de gestión y votación de videos de baloncesto desplegada en AWS. En esta tercera entrega, la arquitectura evoluciona para garantizar alta disponibilidad, escalabilidad automática y distribución de carga, incorporando balanceadores de carga (Load Balancer) y grupos de auto escalado (Auto Scaling Groups) que replican dinámicamente las instancias del backend REST según la demanda.

### Características Principales

- API REST con FastAPI (con auto escalado horizontal)
- Balanceador de carga (Elastic Load Balancer)
- Auto Scaling Group para replicación automática de instancias
- Procesamiento asíncrono de videos con Celery
- Almacenamiento en S3 para videos procesados
- Base de datos PostgreSQL en RDS
- Arquitectura desacoplada para alta disponibilidad

---

## Cambios Arquitectónicos Respecto a la Entrega 2

### 🆕 Nuevos Componentes

#### Load Balancer (ELB - Elastic Load Balancer)

- Actúa como punto de entrada único para todas las peticiones HTTP
- Distribuye el tráfico entre las instancias disponibles del backend REST
- Realiza health checks cada 20 segundos al puerto 8000
- Proporciona un DNS público único (endpoint) para los clientes

#### Target Group

- Agrupa las instancias del backend REST que están activas
- Define el puerto de acceso (8000) para las peticiones
- Monitorea el estado de salud de cada instancia
- Solo enruta tráfico a instancias "healthy"

#### Auto Scaling Group (ASG)

- Crea y destruye instancias EC2 del backend REST automáticamente
- Configurado para escalar entre 1 y 3 instancias
- Utiliza un Launch Template con User Data script
- Distribuye instancias en múltiples zonas de disponibilidad (us-east-1a y us-east-1b)

### 🔄 Componentes Modificados

#### Backend REST

- **Antes**: Una única instancia EC2 manual
- **Ahora**: Múltiples instancias (1-3) creadas automáticamente por el ASG
- Cada instancia ejecuta el mismo código con Docker Compose
- Las instancias son stateless (sin estado compartido entre ellas)
- Dockerizado completamente (sin ambiente virtual de Python)

#### Almacenamiento

- **Antes**: NFS compartido entre backend y worker
- **Ahora**: S3 Bucket para almacenamiento de videos procesados
- **Razón del cambio**: Las instancias auto escaladas no pueden depender de un NFS que se puede desmontar

### ✅ Componentes Sin Cambios

- **Worker Celery**: Sigue en su propia instancia EC2 (subred privada)
- **Base de Datos RDS**: PostgreSQL sin modificaciones
- **Comunicación Backend-Worker**: Sigue siendo indirecta mediante polling de la base de datos

---

## Arquitectura de Despliegue en AWS (Entrega 3)

La arquitectura ahora se compone de 6 componentes principales:

### 1️⃣ Load Balancer - ELB (Elastic Load Balancer)

- **Tipo**: Application Load Balancer (HTTP/HTTPS)
- **Función**: Punto de entrada único y distribución de carga
- **Responsabilidades**:
  - Recibir todas las peticiones HTTP de los clientes
  - Distribuir el tráfico entre las instancias backend disponibles
  - Realizar health checks periódicos (cada 20 segundos)
  - Enrutar solo a instancias "healthy"
- **Puerto**: 80 (HTTP) → redirige al puerto 8000 de las instancias
- **DNS Público**: Endpoint único para acceso externo
- **Target Group Asociado**: backend-rest-target-group

### 2️⃣ Target Group

- **Nombre**: backend-rest-target-group
- **Función**: Agrupar las instancias del backend REST
- **Configuración**:
  - Puerto de destino: 8000
  - Protocolo: HTTP
  - Health check: GET al puerto 8000
  - Intervalo de health check: 20 segundos
- **Instancias Registradas**: Automáticamente gestionadas por el ASG

### 3️⃣ Auto Scaling Group (ASG)

- **Nombre**: backend-rest-asg
- **Función**: Crear y destruir instancias del backend REST automáticamente
- **Configuración**:
  - Capacidad mínima: 1 instancia
  - Capacidad deseada: 2 instancias
  - Capacidad máxima: 3 instancias
  - Zonas de disponibilidad: us-east-1a, us-east-1b
  - Launch Template: backend-rest-launch-template
- **Política de Escalado**:
  - Métrica: Uso de CPU
  - Umbral de escalado hacia arriba: 50% CPU
  - Umbral de escalado hacia abajo: 20% CPU
  - Cooldown: 300 segundos (5 minutos)

### 4️⃣ Instancias EC2 - Backend REST (Réplicas del ASG)

- **Cantidad**: 1 a 3 instancias (dinámico)
- **Tipo de instancia**: t2.micro (o según configuración del Launch Template)
- **Servicio**: FastAPI (Dockerizado)
- **Función**: Exponer endpoints de la API REST
- **Responsabilidades** (cada instancia):
  - Autenticación de usuarios (signup/login)
  - Gestión de videos (upload/consulta/eliminación)
  - Sistema de votación y ranking
  - Recepción y almacenamiento de archivos en S3
  - Escritura en la base de datos RDS
- **Características Importantes**:
  - **Stateless**: No mantienen estado entre peticiones
  - **Idénticas**: Todas ejecutan el mismo código
  - **Efímeras**: Pueden ser creadas o destruidas en cualquier momento
  - **Dockerizadas**: Ejecutan contenedores con Docker Compose
- **Despliegue Automático**:
  - User Data script ejecutado al crear cada instancia
  - Instala Docker y Docker Compose
  - Clona el repositorio desde GitHub
  - Crea archivo `.env` con variables de entorno
  - Levanta contenedores con `docker-compose up -d`
- **Puerto Expuesto**: 8000 (FastAPI)
- **Acceso**: Solo a través del Load Balancer

### 5️⃣ Instancia EC2 - Worker Celery (Sin Cambios)

- **Servicio**: Celery Worker
- **Función**: Procesamiento asíncrono de videos
- **Responsabilidades**:
  - Revisión periódica de la base de datos (cada 1 minuto)
  - Encolamiento de tareas de procesamiento
  - Procesamiento de videos (conversión, marca de agua con FFmpeg)
  - Actualización del estado de videos en la BD
  - Subida de videos procesados a S3
- **Ubicación**: Subred privada (sin acceso público directo)

### 6️⃣ Instancia RDS - Base de Datos PostgreSQL (Sin Cambios)

- **Servicio**: Amazon RDS (PostgreSQL)
- **Función**: Persistencia de datos
- **Almacena**:
  - Usuarios (credenciales, información personal)
  - Videos (metadata, URLs, estado de procesamiento)
  - Votos (relación usuario-video)
- **Acceso**: Desde instancias del backend REST y Worker

### 7️⃣ S3 Bucket - Almacenamiento de Videos

- **Nombre del Bucket**: (configurado en variables de entorno)
- **Función**: Almacenamiento persistente de videos
- **Estructura**:
  - `original_videos/`: Videos subidos por usuarios
  - `processed_videos/`: Videos procesados con marca de agua
- **Acceso**:
  - **Backend REST**: Escritura (upload de videos originales)
  - **Worker**: Lectura y escritura (descarga originales, sube procesados)
  - **Credenciales**: Mediante IAM Roles asociados a las instancias EC2

---

## Diagramas

### Diagrama de Componentes (Entrega 3)


El diagrama muestra:

- Cliente HTTP conectado al Load Balancer
- Load Balancer conectado al Target Group
- Target Group conteniendo múltiples instancias Backend REST (creadas por ASG)
- Instancias Backend REST comunicándose con:
  - Base de datos RDS PostgreSQL
  - Bucket S3 para almacenamiento
- Worker independiente comunicándose con:
  - Base de datos RDS PostgreSQL (polling)
  - Bucket S3 (lectura y escritura)

### Diagrama de Despliegue (Entrega 3)


El diagrama de despliegue ilustra la distribución física de los componentes en la infraestructura de AWS:

**Componentes de Infraestructura:**

- **VPC AWS**: Contenedor principal que encapsula toda la infraestructura del sistema
- **Subred Pública**: Red dentro del VPC que aloja todos los componentes con acceso a Internet

**Componentes de Aplicación:**

- **AWS-ELB + Auto Scaling Group**: Punto de entrada que balancea la carga y gestiona el escalado automático de instancias Backend
- **Instancias EC2 Backend (Ubuntu 24.04)**: Múltiples máquinas virtuales (hasta 3) ejecutando la aplicación FastAPI (ANB-App), creadas dinámicamente por el ASG
- **AWS-RDS**: Servicio de base de datos PostgreSQL gestionado (ANBDataBase) para persistencia de datos
- **AWS-EC2 Worker (Ubuntu 24.04)**: Máquina virtual dedicada ejecutando Celery Worker (ProcesadorVideos) para procesamiento asíncrono
- **AWS-S3**: Servicio de almacenamiento de objetos para videos originales y procesados

**Comunicación TCP/IP:**

- Usuario → ELB (entrada de peticiones HTTP)
- ELB → Instancias Backend (distribución de carga mediante líneas punteadas)
- Instancias Backend → RDS y S3 (lectura/escritura de datos y archivos)
- Worker → RDS y S3 (polling de tareas y procesamiento de videos)

> **Nota**: Todas las instancias Backend son idénticas y stateless, permitiendo que el Auto Scaling Group las cree o destruya según la demanda sin afectar el servicio.

## Flujo de Peticiones con Load Balancer

### 📱 Fase 1: Cliente realiza petición

1. Cliente HTTP envía petición (ej: `POST /api/videos/upload`)
2. La petición llega al DNS del Load Balancer (endpoint público)

### ⚖️ Fase 2: Load Balancer distribuye la carga

1. Load Balancer recibe la petición
2. Consulta el Target Group para obtener las instancias disponibles
3. Selecciona una instancia "healthy" del grupo (algoritmo round-robin o least connections)
4. Envía la petición al puerto 8000 de la instancia seleccionada

**Ejemplo de distribución de carga:**
```
Petición 1 → Load Balancer → Instancia 1 (10.0.1.15:8000)
Petición 2 → Load Balancer → Instancia 2 (10.0.1.22:8000)
Petición 3 → Load Balancer → Instancia 3 (10.0.1.38:8000)
Petición 4 → Load Balancer → Instancia 1 (10.0.1.15:8000)
...
```

### 🖥️ Fase 3: Instancia Backend procesa la petición

1. La instancia seleccionada recibe la petición en su puerto 8000
2. FastAPI procesa la petición:
   - Valida token de autenticación (JWT)
   - Guarda el video en S3 Bucket (`original_videos/`)
   - Registra la metadata en RDS PostgreSQL
3. La instancia devuelve la respuesta al Load Balancer
4. El Load Balancer reenvía la respuesta al cliente

> **Nota importante**: Las instancias son stateless, por lo que cada petición puede ser procesada por cualquier instancia sin importar el orden.

---

## Flujo de Procesamiento de Videos (Sin Cambios Respecto a Entrega 2)

### ⚙️ Fase 1: Worker detecta videos pendientes

1. El Worker Celery ejecuta una tarea periódica cada 1 minuto
2. Consulta la base de datos RDS para buscar videos con `status = 'UPLOADED'`
3. Por cada video encontrado, encola una tarea de procesamiento

### 🎬 Fase 2: Worker procesa el video

1. Descarga el video original desde S3 (`original_videos/`)
2. Procesa el video:
   - Conversión de formato
   - Añade marca de agua con FFmpeg
3. Sube el video procesado a S3 (`processed_videos/`)
4. Actualiza el registro en la base de datos:
   - `status = 'PROCESSED'`
   - `processed_url`: URL del video procesado en S3

---

## Mecanismo de Auto Escalado

### 📈 Escenarios de Escalado Automático

#### Escalado Horizontal hacia Arriba (Scale Out)

**Trigger**: Uso de CPU > 50% durante 2 minutos consecutivos

**Proceso**:

1. CloudWatch detecta alta utilización de CPU en las instancias actuales
2. Auto Scaling Group decide crear una nueva instancia
3. Se crea una nueva instancia EC2 usando el Launch Template
4. El User Data script se ejecuta automáticamente
5. La instancia comienza a exponer el puerto 8000
6. El Target Group realiza health checks
7. Una vez que la instancia pasa los health checks, se marca como "healthy"
8. El Load Balancer comienza a enviar tráfico a la nueva instancia

**Resultado**: El sistema ahora puede manejar más peticiones concurrentes.


### 🏥 Health Checks y Recuperación Automática

**Configuración del Health Check:**

- **Tipo**: HTTP GET
- **Puerto**: 8000
- **Path**: `/` (o endpoint específico de health)
- **Intervalo**: 20 segundos
- **Timeout**: 5 segundos
- **Intentos fallidos para marcar unhealthy**: 2 consecutivos
- **Intentos exitosos para marcar healthy**: 2 consecutivos

**Escenario de Recuperación:**

1. Una instancia deja de responder correctamente (fallo en la aplicación, contenedor caído, etc.)
2. El Target Group detecta 2 health checks fallidos consecutivos (40 segundos)
3. La instancia se marca como "unhealthy"
4. El Load Balancer deja de enviar tráfico a esa instancia
5. El Auto Scaling Group detecta la instancia unhealthy
6. Opcionalmente, el ASG puede:
   - Esperar a que se recupere
   - Terminar la instancia y crear una nueva

**Resultado**: El sistema mantiene alta disponibilidad incluso cuando instancias individuales fallan.


## Ventajas de la Nueva Arquitectura

### ✅ Alta Disponibilidad

- Si una instancia falla, el Load Balancer redirige el tráfico a las instancias sanas
- El Auto Scaling Group reemplaza automáticamente instancias fallidas
- Las instancias están distribuidas en múltiples zonas de disponibilidad

### ✅ Escalabilidad Horizontal Automática

- El sistema escala automáticamente según la demanda (CPU)
- Puede manejar picos de tráfico sin intervención manual
- Reduce costos durante periodos de baja demanda

### ✅ Distribución de Carga

- Las peticiones se distribuyen equitativamente entre las instancias disponibles
- Ninguna instancia individual se sobrecarga
- Mejor experiencia de usuario (menor latencia)

### ✅ Despliegue Simplificado

- El User Data script automatiza la configuración de nuevas instancias
- No se requiere configuración manual de cada instancia
- Consistencia garantizada entre todas las instancias

### ✅ Stateless Architecture

- Las instancias no mantienen estado local
- Cualquier instancia puede manejar cualquier petición
- Facilita el auto escalado y la recuperación ante fallos


## Comparación: Entrega 2 vs Entrega 3

| Aspecto | Entrega 2 | Entrega 3 |
|---------|-----------|-----------|
| **Punto de Entrada** | IP pública de instancia única | DNS del Load Balancer |
| **Número de Instancias Backend** | 1 (fija) | 1-3 (dinámico) |
| **Disponibilidad** | SPOF (Single Point of Failure) | Alta disponibilidad (múltiples instancias) |
| **Escalabilidad** | Manual (crear instancia manualmente) | Automática (ASG) |
| **Distribución de Carga** | Una instancia maneja todo | Load Balancer distribuye el tráfico |
| **Recuperación ante Fallos** | Manual (requiere intervención) | Automática (ASG reemplaza instancias) |
| **Almacenamiento de Videos** | NFS compartido | S3 Bucket |
| **Despliegue** | Manual (SSH + comandos) | Automático (User Data script) |
| **Costos** | Fijos (~$1/día) | Variables según carga (~$1.50-$2/día) |


## Conclusión

La arquitectura de la Entrega 3 representa una evolución significativa hacia un sistema altamente disponible, escalable y resiliente. La introducción del Load Balancer y el Auto Scaling Group permite que el sistema ANB Rising Stars maneje cargas variables de tráfico de manera eficiente, manteniendo una experiencia de usuario consistente incluso durante picos de demanda.

Aunque esta configuración introduce mayor complejidad operacional y costos variables, las ventajas en términos de disponibilidad y escalabilidad justifican la inversión para un sistema en producción.

---

**Documentación actualizada**: 09 de noviembre de 2025 
**Versión**: 3.0 (AWS con Load Balancer y Auto Scaling)  