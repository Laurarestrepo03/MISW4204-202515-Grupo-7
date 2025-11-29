# Arquitectura Entrega 5 del Sistema - ANB

## Descripción General
El sistema ANB es una plataforma de gestión y votación de videos de baloncesto desplegada en AWS. En esta quinta entrega, la arquitectura evoluciona para adoptar un modelo **Platform as a Service (PaaS)** utilizando **Amazon ECS (Elastic Container Service) con AWS Fargate**, reemplazando las instancias EC2 por contenedores gestionados, tanto en el backend como en los workers de procesamiento.

### Características Principales

- API REST con FastAPI desplegada en **🆕 ECS con Fargate**
- Balanceador de carga (Application Load Balancer) **solo para el backend**
- **🆕 ECS Service para backend con tareas auto-escalables**
- **🆕 ECS Service para workers con tareas auto-escalables**
- **🆕 Workers SIN balanceador de carga** (no requieren interacción directa con usuarios)
- **🆕 Imágenes Docker almacenadas en Amazon ECR**
- Procesamiento asíncrono de videos con AWS SQS
- Almacenamiento en S3 para videos originales y procesados
- Base de datos PostgreSQL en RDS (Multi-AZ)
- Arquitectura completamente serverless y escalable

---

## Cambios Arquitectónicos Respecto a la Entrega 4

### 🆕 Nuevos Componentes

#### Amazon ECS (Elastic Container Service)

- **Tipo de lanzamiento**: AWS Fargate (serverless)
- **Función**: Ejecutar contenedores Docker sin necesidad de gestionar servidores
- **Ventajas sobre EC2**:
  - No hay que aprovisionar ni gestionar instancias
  - Escalado automático a nivel de contenedor
  - Pago solo por recursos utilizados (vCPU y memoria)
  - Despliegue más rápido y consistente
  - Sin necesidad de parches de sistema operativo

#### Amazon ECR (Elastic Container Registry)

- **Función**: Almacenar imágenes Docker del backend y worker
- **Repositorios**:
  - `anb-backend`: Imagen Docker de la API REST (FastAPI)
  - `anb-worker`: Imagen Docker del worker SQS
- **Integración**: Las tareas ECS descargan las imágenes directamente desde ECR

#### ECS Cluster

- **Nombre**: `anb-cluster`
- **Tipo**: Fargate (sin instancias EC2 subyacentes)
- **Función**: Agrupar y gestionar los servicios de backend y worker
- **Contenido**: 
  - ECS Service: Web (Backend REST)
  - ECS Service: Worker (Procesamiento de videos)

#### ECS Services (Servicios)

Los servicios ECS son agrupadores lógicos que gestionan las tareas y garantizan que siempre haya un número determinado de tareas ejecutándose.

**Servicio Web (Backend REST)**:
- **Nombre**: `anb-web-service`
- **Función**: Gestionar las tareas del backend REST
- **Asociaciones**: 
  - Target Group del Application Load Balancer
  - Auto Scaling configurado
- **Tareas deseadas**: 1-3

**Servicio Worker**:
- **Nombre**: `anb-worker-service`
- **Función**: Gestionar las tareas del worker de procesamiento
- **Asociaciones**: 
  - Auto Scaling configurado (basado en CPU)
  - **SIN Load Balancer** (no requiere interacción HTTP directa)
- **Tareas deseadas**: 1-3

#### ECS Tasks (Tareas)

Las tareas son las unidades de ejecución que contienen los contenedores Docker. **Las tareas están dentro de los servicios, y los servicios dentro del cluster**.

**Estructura jerárquica**:
```
ECS Cluster
├── ECS Service: Web
│   ├── Web Task 1 (contenedor: anb-backend)
│   └── Web Task 2 (contenedor: anb-backend)
└── ECS Service: Worker
    ├── Worker Task 1 (contenedor: anb-worker)
    └── Worker Task 2 (contenedor: anb-worker)
```

**Configuración de las tareas**:
- **CPU**: 2 vCPU (mínimo requerido por Fargate para esta configuración)
- **Memoria**: 4 GB RAM
- **Almacenamiento**: 20 GB (efímero)
- **Red**: Cada tarea tiene su propia IP privada (y pública si está en subnet pública)

### 🔄 Componentes Modificados

#### Backend REST → ECS Tasks

- **Antes (Entrega 4)**: Instancias EC2 en Auto Scaling Group
- **Ahora (Entrega 5)**: **Tareas ECS en Fargate** dentro del servicio Web
- **Puerto expuesto**: 8000 (FastAPI)
- **Imagen Docker**: Desde ECR (`anb-backend`)

#### Workers de Procesamiento → ECS Tasks

- **Antes (Entrega 4)**: Instancias EC2 en Auto Scaling Group con Load Balancer para health checks
- **Ahora (Entrega 5)**: **Tareas ECS en Fargate** dentro del servicio Worker
- **Cambios clave**:
  - **Eliminado**: Load Balancer para workers (ya no es necesario)
  - **Eliminado**: Puerto 80 para health checks (ECS gestiona la salud de las tareas)
  - **Mantenido**: Auto Scaling basado en CPU
- **Imagen Docker**: Desde ECR (`anb-worker`)

#### Load Balancer

- **Antes (Entrega 4)**: Dos Load Balancers (uno para backend, uno para workers)
- **Ahora (Entrega 5)**: **Solo UN Load Balancer para el backend**
- **Razón**: Los workers no necesitan recibir tráfico HTTP externo; solo consumen mensajes de SQS

### ❌ Componentes Eliminados

- **Instancias EC2**: Reemplazadas completamente por tareas ECS Fargate
- **Auto Scaling Groups (ASG)**: Reemplazados por ECS Service Auto Scaling
- **Launch Templates**: Ya no son necesarios (Fargate gestiona la infraestructura)
- **Load Balancer para Workers**: Los workers no requieren health checks HTTP externos
- **User Data Scripts**: Las imágenes Docker ya contienen toda la configuración

---

## Arquitectura de Despliegue en AWS (Entrega 5)

La arquitectura ahora se compone de los siguientes componentes principales:

### 1️⃣ Application Load Balancer (ALB)

- **Función**: Punto de entrada único para el backend REST
- **Target Group**: `anb-web-target-group`
- **Targets**: Tareas del ECS Service Web (IPs dinámicas)
- **Puerto**: 80 (HTTP) → redirige a puerto 8000 de las tareas
- **Health Check**: `/api/health` en puerto 8000
- **Nota**: **Solo conectado al backend**, NO a los workers

### 2️⃣ Amazon ECR (Elastic Container Registry)

- **Repositorios**:
  - `anb-backend`: Imagen del backend FastAPI
  - `anb-worker`: Imagen del worker SQS
- **Flujo de despliegue**:
  1. Se construye la imagen Docker localmente o en una instancia temporal
  2. Se autentica con ECR usando AWS CLI
  3. Se hace `docker push` de la imagen al repositorio
  4. Las tareas ECS descargan la imagen desde ECR

### 3️⃣ ECS Cluster - Fargate

- **Nombre**: `anb-cluster`
- **Tipo de lanzamiento**: Fargate (serverless)
- **Función**: Contenedor lógico para todos los servicios ECS
- **Ubicación**: VPC con subnets privadas

### 4️⃣ ECS Service: Web (Backend REST)

- **Nombre**: `anb-web-service`
- **Task Definition**: `anb-backend-task`
- **Configuración de la tarea**:
  - **CPU**: 2 vCPU
  - **Memoria**: 4 GB
  - **Almacenamiento**: 20 GB
  - **Puerto**: 8000
  - **Imagen**: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/anb-backend:latest`
- **Capacidad**:
  - Mínimo: 1 tarea
  - Deseado: 1-2 tareas
  - Máximo: 3 tareas
- **Asociaciones**:
  - Application Load Balancer (Target Group)
  - Auto Scaling (Target Tracking al 50% CPU)
- **Red**: Subnets privadas con NAT Gateway para acceso a internet

### 5️⃣ ECS Service: Worker (Procesamiento de Videos)

- **Nombre**: `anb-worker-service`
- **Task Definition**: `anb-worker-task`
- **Configuración de la tarea**:
  - **CPU**: 2 vCPU
  - **Memoria**: 4 GB
  - **Almacenamiento**: 20 GB
  - **Puerto**: Ninguno expuesto (no requiere tráfico entrante)
  - **Imagen**: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/anb-worker:latest`
- **Capacidad**:
  - Mínimo: 1 tarea
  - Deseado: 1-2 tareas
  - Máximo: 3 tareas
- **Auto Scaling**: Target Tracking al 50% CPU
  - Cuando CPU promedio > 50%: Se crean nuevas tareas
  - Cuando CPU promedio < 50%: Se terminan tareas excedentes
- **Sin Load Balancer**: Los workers no necesitan recibir tráfico HTTP
- **Función**: Consumir mensajes de SQS y procesar videos

**¿Por qué los workers no tienen Load Balancer?**

En la Entrega 4, el Load Balancer de los workers se usaba para realizar health checks y detectar instancias no saludables. En ECS Fargate:
- ECS gestiona automáticamente la salud de las tareas
- Si una tarea falla, ECS la reemplaza automáticamente
- Los workers solo necesitan acceso de salida (a SQS, S3, RDS)
- No necesitan recibir tráfico HTTP entrante

### 6️⃣ AWS SQS - Cola de Mensajes

- **Sin cambios** respecto a Entrega 4
- **Nombre de la cola**: `ANB_SQS`
- **Función**: Almacenar mensajes con IDs de videos pendientes de procesamiento
- **Acceso**:
  - **Backend (ECS Tasks Web)**: Escritura (envío de mensajes)
  - **Workers (ECS Tasks Worker)**: Lectura y eliminación de mensajes

### 7️⃣ Amazon RDS - Base de Datos PostgreSQL

- **Sin cambios** respecto a Entrega 4
- **Configuración**: Multi-AZ para alta disponibilidad
- **Acceso**: Desde las tareas ECS (backend y worker) a través de la VPC

### 8️⃣ Amazon S3 - Almacenamiento de Videos

- **Sin cambios** respecto a Entrega 4
- **Estructura**:
  - `original_videos/`: Videos subidos por usuarios
  - `processed_videos/`: Videos procesados con marca de agua

### 9️⃣ Componentes de Red

- **VPC**: Virtual Private Cloud con subnets públicas y privadas
- **Internet Gateway**: Para acceso desde internet al ALB
- **NAT Gateway**: Para que las tareas en subnets privadas accedan a internet (S3, SQS, ECR)
- **Security Groups**: Controlan el tráfico entre componentes

---

## Diagramas

### Diagrama de Componentes (Entrega 5)

El diagrama muestra:

- **Cliente HTTP** conectado al **Application Load Balancer**
- **Load Balancer** conectado al **Target Group** del ECS Service Web
- **ECS Cluster** conteniendo:
  - **ECS Service: Web** con múltiples **Web Tasks** (contenedores FastAPI)
  - **ECS Service: Worker** con múltiples **Worker Tasks** (contenedores de procesamiento)
- **Web Tasks** comunicándose con:
  - Base de datos RDS PostgreSQL
  - Bucket S3
  - Cola SQS (envío de mensajes)
- **Cola SQS** como componente independiente
- **Worker Tasks** escuchando la cola SQS (polling)
- **Worker Tasks** comunicándose con:
  - Base de datos RDS PostgreSQL (actualización de estado)
  - Bucket S3 (lectura de originales, escritura de procesados)
- **Amazon ECR** almacenando las imágenes Docker

### Diagrama de Despliegue (Entrega 5)

El diagrama de despliegue ilustra:

---

## Flujo de Peticiones y Procesamiento (Entrega 5)

### 📱 Fase 1: Usuario sube un video

1. Cliente envía `POST /api/videos/upload` al DNS del Application Load Balancer
2. Load Balancer distribuye la petición a una **tarea del ECS Service Web**
3. La tarea backend:
   - Valida el token JWT
   - Sube el video a S3 (`original_videos/`)
   - Crea registro en PostgreSQL con `status = 'UPLOADED'`
   - Envía mensaje a SQS con el `video_id`
   - Devuelve respuesta al cliente

### ⚙️ Fase 2: Worker procesa el video

1. Una **tarea del ECS Service Worker** recibe el mensaje de SQS mediante long polling
2. La tarea worker extrae el `video_id` del mensaje
3. Descarga el video original desde S3
4. Procesa el video (conversión + marca de agua con FFmpeg)
5. Sube el video procesado a S3 (`processed_videos/`)
6. Actualiza el registro en PostgreSQL (`status = 'PROCESSED'`)
7. Elimina el mensaje de SQS

### 🔄 Fase 3: Auto Scaling de Tareas ECS

**Escenario 1: Muchos videos subidos simultáneamente**
1. Se acumulan mensajes en la cola SQS
2. Las tareas worker procesan videos intensivamente (FFmpeg usa mucho CPU)
3. El CPU promedio de las tareas worker sube a 80-90%
4. ECS Service Auto Scaling detecta CPU > 50% sostenido
5. Se crean nuevas tareas worker automáticamente
6. Las nuevas tareas comienzan a consumir mensajes de SQS
7. La carga se distribuye entre más tareas

**Escenario 2: No hay videos pendientes**
1. Cola SQS vacía → Workers en idle
2. CPU promedio: ~5-10% (solo escuchando SQS)
3. ECS Service Auto Scaling detecta CPU < 50% sostenido
4. Se terminan tareas excedentes
5. Solo quedan las tareas mínimas (1), optimizando costos

---

## Mecanismo de Auto Escalado en ECS Fargate

### 📊 ECS Service Auto Scaling

El escalado en ECS Fargate funciona a nivel de **tareas**, no de instancias:

**Configuración para ambos servicios**:
- **Tipo**: Target Tracking Scaling
- **Métrica**: `ECSServiceAverageCPUUtilization`
- **Valor objetivo**: 50%
- **Capacidad mínima**: 1 tarea
- **Capacidad máxima**: 3 tareas

**Proceso de escalado**:

**Scale Out (Agregar Tareas)**:
1. CloudWatch monitorea la utilización de CPU de las tareas
2. Cuando el promedio supera el 50%, ECS crea nuevas tareas
3. Las nuevas tareas se registran automáticamente:
   - **Web Tasks**: En el Target Group del ALB
   - **Worker Tasks**: Comienzan a consumir de SQS
4. La carga se distribuye, reduciendo el CPU promedio

**Scale In (Quitar Tareas)**:
1. CloudWatch detecta CPU bajo de forma sostenida
2. ECS determina que hay capacidad de sobra
3. Se terminan tareas excedentes (una a la vez)
4. Se mantiene al menos 1 tarea por servicio

### 🏥 Health Checks en ECS

**Para Web Tasks (Backend)**:
- El ALB realiza health checks al endpoint `/api/health`
- Si una tarea no responde, el ALB deja de enviarle tráfico
- ECS detecta la tarea no saludable y la reemplaza

**Para Worker Tasks**:
- ECS monitorea el estado del contenedor
- Si el contenedor falla o se detiene, ECS lo reemplaza automáticamente
- No se requiere health check HTTP (los workers no exponen puertos)

---

## Ventajas de la Nueva Arquitectura (Entrega 5)

### ✅ Comparado con EC2 (Entrega 4)

| Aspecto | EC2 (Entrega 4) | ECS Fargate (Entrega 5) |
|---------|-----------------|-------------------------|
| **Gestión de servidores** | Hay que gestionar instancias | Completamente serverless |
| **Escalado** | A nivel de instancias (más lento) | A nivel de contenedores (más rápido) |
| **Costo** | Pago por instancia (incluso si idle) | Pago por uso real (vCPU/memoria) |
| **Despliegue** | User Data scripts | Imágenes Docker en ECR |
| **Mantenimiento** | Parches de SO, actualizaciones | Cero mantenimiento de infraestructura |
| **Consistencia** | Depende de scripts | Contenedores inmutables |
| **Tiempo de escalado** | ~2-3 minutos (nueva EC2) | ~30-60 segundos (nueva tarea) |

### ✅ Arquitectura Serverless

- **Fargate** elimina la necesidad de gestionar la infraestructura subyacente
- No hay que seleccionar tipos de instancia ni capacidad
- AWS gestiona automáticamente los recursos computacionales
- Ideal para cargas de trabajo con demanda variable

### ✅ Contenedores Inmutables

- Las imágenes Docker garantizan consistencia entre entornos
- Despliegues reproducibles y predecibles
- Fácil rollback a versiones anteriores
- CI/CD simplificado

### ✅ Simplificación de Workers

- Sin Load Balancer para workers (menos componentes)
- ECS gestiona automáticamente la salud de las tareas
- Los workers solo necesitan acceso de salida
- Menor complejidad y menor costo

---

## Comparación: Entrega 4 vs Entrega 5

| Aspecto | Entrega 4 (EC2) | Entrega 5 (ECS Fargate) |
|---------|-----------------|-------------------------|
| **Infraestructura Backend** | EC2 en ASG | ECS Tasks en Fargate |
| **Infraestructura Workers** | EC2 en ASG | ECS Tasks en Fargate |
| **Load Balancer Backend** | Sí (ALB) | Sí (ALB) |
| **Load Balancer Workers** | Sí (para health checks) | **No** (ECS gestiona la salud) |
| **Registro de Imágenes** | N/A (instalación via User Data) | Amazon ECR |
| **Escalado** | ASG (a nivel de instancia) | ECS Service Auto Scaling (a nivel de tarea) |
| **Tiempo de despliegue** | ~2-3 min (nueva instancia) | ~30-60 seg (nueva tarea) |
| **Gestión de OS** | Manual (parches, actualizaciones) | Gestionado por AWS |
| **Modelo de costos** | Por instancia/hora | Por vCPU/memoria/segundo |
| **SQS** | Sin cambios | Sin cambios |
| **RDS** | Sin cambios | Sin cambios |
| **S3** | Sin cambios | Sin cambios |

---


## Conclusión

La arquitectura de la Entrega 5 representa la evolución hacia un modelo **Platform as a Service (PaaS)** completamente serverless utilizando **Amazon ECS con AWS Fargate**. Esta transición elimina la necesidad de gestionar instancias EC2, simplifica los despliegues mediante contenedores Docker inmutables, y proporciona una arquitectura más moderna, escalable y económica.

Los principales beneficios incluyen:

1. **Eliminación de gestión de servidores**: Fargate gestiona toda la infraestructura subyacente
2. **Escalado más rápido**: Las tareas ECS se crean en segundos, no minutos
3. **Simplificación de workers**: Sin Load Balancer adicional para health checks
4. **Despliegues consistentes**: Imágenes Docker inmutables desde ECR
5. **Optimización de costos**: Pago por uso real de recursos (vCPU y memoria)

Esta arquitectura mantiene todas las ventajas de la Entrega 4 (SQS, desacoplamiento, auto scaling) mientras añade los beneficios de una plataforma completamente gestionada.

---

**Documentación actualizada**: 29 de noviembre de 2025  
**Versión**: 5.0 (PaaS con ECS Fargate)

