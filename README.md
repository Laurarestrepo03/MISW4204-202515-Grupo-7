## Pasos para Ejecutar la Aplicación

### 1. Crear el Ambiente Virtual
```bash
python -m venv venv
```

### 2. Activar el Ambiente Virtual
**En Windows:**
```bash
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar las Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar la Base de Datos (Solo la Primera Vez)
**NOTA:** Antes de ejecutar este script, asegúrate de configurar la contraseña de PostgreSQL en `setup_local_db.py` y `database.py` según tu instalación local.

```bash
python setup_local_db.py
```

Este script crea la base de datos `anb` y las tablas necesarias. Solo necesitas ejecutarlo una vez.

### 5. Montar Docker
```bash
docker-compose up -d
```

### 6. Iniciar el Servicio de Celery
**IMPORTANTE:** Este paso debe ejecutarse ANTES de correr la aplicación Uvicorn. Los videos que se intenten procesar sin tener Celery corriendo no se procesarán.

```bash
celery -A tasks worker -l info -P solo
```

### 7. Iniciar la Aplicación Uvicorn
En una nueva terminal (manteniendo Celery corriendo):
```bash
uvicorn main:app --reload
```

## Scripts de Base de Datos

### Configuración Inicial
```bash
python setup_local_db.py
```
Crea la base de datos `anb` y las tablas por primera vez. Si ya existen, no hace cambios.

### Reiniciar Base de Datos
```bash
python reset_db.py
```
⚠️ **ADVERTENCIA:** Este script borra completamente la base de datos `anb` y todos sus datos, luego la vuelve a crear desde cero. Úsalo solo cuando quieras empezar de nuevo con una base de datos limpia.

## Análisis de Calidad de Código con SonarCloud

El proyecto utiliza **SonarCloud** para análisis automático de calidad de código, detectando bugs, vulnerabilidades de seguridad, code smells y midiendo la cobertura de tests.

### 📊 Ver Reportes de SonarCloud

Puedes acceder a los reportes de calidad de código en:

**[https://sonarcloud.io/organizations/misw4204-202515-grupo-7/projects](https://sonarcloud.io/organizations/misw4204-202515-grupo-7/projects)**

O directamente al proyecto específico:

**[https://sonarcloud.io/project/overview?id=misw4204-202515-grupo-7](https://sonarcloud.io/project/overview?id=misw4204-202515-grupo-7)**

### 🔄 Análisis Automático

El análisis de SonarCloud se ejecuta **automáticamente** mediante GitHub Actions en los siguientes casos:

- ✅ Cada `push` a la rama `main` o `develop`
- ✅ Cada `pull request` (abierto, sincronizado o reabierto)

Después de cada push a `main`, se genera un nuevo reporte con las métricas actualizadas del proyecto, incluyendo:
- Bugs detectados
- Vulnerabilidades de seguridad
- Code smells (problemas de mantenibilidad)
- Cobertura de tests
- Duplicación de código


## Integrantes del Equipo
Nombre | Correo Uniandes 
-|-
Julián Felipe Daza Rendón | jf.dazar1@uniandes.edu.co
Juan Camilo Hernández Saavedra | jc.hernandezs1@uniandes.edu.co
Nicolás Javier Jaramillo Cely | nj.jaramillo@uniandes.edu.co
Laura María Restrepo Palomino | l.restrepop@uniandes.edu.co

