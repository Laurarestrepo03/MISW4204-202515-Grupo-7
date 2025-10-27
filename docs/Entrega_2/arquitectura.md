# Arquitectura Entrega 2 del Sistema - ANB 

## Descripción General

El sistema ANB es una plataforma de gestión y votación de videos de baloncesto desplegada en AWS. La arquitectura está distribuida en múltiples instancias EC2 y servicios gestionados para garantizar escalabilidad, disponibilidad y separación de responsabilidades.

### Características Principales
- API REST con FastAPI
- Procesamiento asíncrono de videos con Celery
- Almacenamiento compartido mediante NFS
- Base de datos PostgreSQL en RDS
- Arquitectura desacoplada para alta disponibilidad

---

## Arquitectura de Despliegue en AWS

La arquitectura se compone de **4 componentes principales** distribuidos en diferentes instancias:

### 1️⃣ **Instancia EC2 - Backend REST (Subred Pública)**
- **Servicio**: FastAPI
- **Función**: Exponer endpoints de la API REST
- **Responsabilidades**:
  - Autenticación de usuarios (signup/login)
  - Gestión de videos (upload/consulta/eliminación)
  - Sistema de votación y ranking
  - Recepción de archivos de video
  - Escritura inicial en la base de datos
- **Acceso**: Internet público (API REST)

### 2️⃣ **Instancia EC2 - Worker Celery (Subred Privada)**
- **Servicio**: Celery Worker
- **Función**: Procesamiento asíncrono de videos
- **Responsabilidades**:
  - Revisión periódica de la base de datos (cada 1 minuto)
  - Encolamiento de tareas de procesamiento
  - Procesamiento de videos (conversión, marca de agua)
  - Actualización del estado de videos procesados
- **Acceso**: Sin acceso público directo

### 3️⃣ **Instancia RDS - Base de Datos PostgreSQL**
- **Servicio**: Amazon RDS (PostgreSQL)
- **Función**: Persistencia de datos
- **Almacena**:
  - Usuarios (credenciales, información personal)
  - Videos (metadata, URLs, estado de procesamiento)
  - Votos (relación usuario-video)
- **Acceso**: Solo desde Backend REST y Worker

### 4️⃣ **Instancia EC2 - Almacenamiento NFS (Subred Privada)**
- **Servicio**: Network File System (NFS)
- **Función**: Almacenamiento compartido de archivos
- **Almacena**:
  - Videos originales (`original_videos/`)
  - Videos procesados (`processed_videos/`)
- **Acceso**: Montado en Backend REST y Worker

---

## Diagramas
A continuación se encuentran los diagramas de componentes y despliegue, que también, para una versión de mejor calidad, pueden ser vistos en la carpeta [/diagramas](diagramas/).

### Diagrama de Componentes
<img width="1969" height="1461" alt="image" src="https://github.com/user-attachments/assets/f96f1025-f530-4d0f-ab10-bd1194272a12" />

### Diagrama de Despliegue

<img width="1537" height="1007" alt="diagrama_despliegue" src="https://github.com/user-attachments/assets/58509f5c-a72f-47c0-98f3-049151920adb" />


## Flujo de Procesamiento de Videos

### 📤 **Fase 1: Carga de Video (API REST)**

1. **Usuario crea un video**: El cliente envía una solicitud POST a `/api/videos/upload` con:
   - Archivo de video (MP4)
   - Metadata (título)
   - Token de autenticación

2. **API recibe la solicitud**:
   - Valida el tipo de archivo, duración (20-60s) y tamaño (<100MB)
   - Autentica al usuario mediante JWT token

3. **API guarda el video**:
   - Copia el archivo en la carpeta compartida NFS: `original_videos/`
   - El archivo queda accesible para el Worker

4. **API registra en la base de datos**:
   - Crea una nueva fila en la tabla `Video` con:
     - `title`: Título del video
     - `status`: `UPLOADED` (sin procesar)
     - `uploaded_at`: Timestamp de carga
     - `original_url`: Ruta del video original
     - `user_id`: ID del usuario propietario
     - `task_id`: `NULL` (sin tarea asignada aún)

5. **API finaliza**: Retorna respuesta al cliente con estado 201

---

### ⚙️ **Fase 2: Procesamiento de Video (Worker)**

El Worker ejecuta **dos tipos de tareas** de forma periódica:

**Tarea 1: Revisión de Base de Datos** 

**Tarea 2: Procesamiento de Video**

### 📊 **Estado de las Colas de Celery**

En cualquier momento, el Worker puede tener en su cola:

1. **Tarea de revisión de BD**: Se encola automáticamente cada minuto
2. **Tareas de procesamiento de videos**: Una por cada video pendiente detectado

**Ejemplo de cola**:
```
Cola de Celery:
├── check_unprocessed_videos (ejecutándose)
├── process_video (video_id=123)
├── process_video (video_id=124)
├── process_video (video_id=125)
└── check_unprocessed_videos (programada para 1 min)
```

---

### **Cambio con arquitectonico con respecto a la version anterior**

### ⚠️ **Backend REST ↔ Worker**: No existe comunicación directa

**Razón del cambio arquitectónico**:

#### **Arquitectura Anterior (Local)**
```
┌─────────────────────────────────────┐
│         Localhost                   │
│  ┌─────────────┐  ┌──────────────┐ │
│  │  API REST   │  │    Worker    │ │
│  │  (FastAPI)  │──│   (Celery)   │ │
│  └─────────────┘  └──────────────┘ │
│         │               │           │
│         └───── Redis ───┘           │
└─────────────────────────────────────┘
```
- ✅ API y Worker en el mismo host
- ✅ Comunicación directa mediante Redis (localhost)
- ✅ API podía encolar tareas directamente

#### **Arquitectura Actual (AWS - Redes Separadas)**
```
┌──────────────────┐      ┌──────────────────┐
│     Subred       │      │      Subred      │
│                  │      │                  │
│  ┌────────────┐  │      │  ┌────────────┐  │
│  │  API REST  │  │      │  │   Worker   │  │
│  │  (FastAPI) │  │      │  │  (Celery)  │  │
│  └────────────┘  │      │  └────────────┘  │
│        │         │      │        │         │
└────────┼─────────┘      └────────┼─────────┘
         │                         │
         └──────── RDS PostgreSQL ──┘
              (Base de Datos Compartida)
```

**Problema encontrado**:
- ❌ Instancias en redes diferentes (VPC)
- ❌ Security Groups bloqueando comunicación directa
- ❌ Redis no accesible entre subredes
- ❌ Latencia y complejidad de configuración

**Solución implementada**:
- ✅ **Polling Pattern**: Worker revisa la BD periódicamente
- ✅ **Base de datos como mediador**: Comunicación asíncrona mediante estado
- ✅ **Desacoplamiento completo**: API y Worker independientes
- ✅ **Mayor resiliencia**: Si un componente falla, el otro sigue funcionando

---
**Documentación actualizada**: 26 de octubre de 2025  
**Versión**: 2.0 (Subido en AWS)

