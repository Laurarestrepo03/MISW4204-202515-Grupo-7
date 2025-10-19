## 🧪 Ejecución de las Pruebas Unitarias
Para ejecutar las pruebas unitarias destinadas a probar el funcionamiento del API, se deben ejecutar los siguientes pasos:

Nota: si ya he hecho las instalaciones previas, salte al [paso 5](#5-iniciar-la-aplicación-uvicorn), y si ya está ejecutando la aplicación, salte al [paso 6](#6-parar-el-servicio-de-celery).

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

### 4. Montar Docker
```bash
docker-compose up -d
```

### 5. Iniciar la Aplicación Uvicorn
```bash
uvicorn main:app --reload
```

### 6. Parar el Servicio de Celery
Si tiene uno o varios servicios de Celery corriendo, termínelos **todos** en la terminal donde se estén ejecutando. Esto lo puede hacer con `ctrl+C` en Windows o `cmd+C` en Mac.

### 7. Correr las Pruebas
En una nueva terminal:
```bash
pytest
```

### 8. Observar los Resultados
Una vez se hayan terminado de ejcutar las pruebas, debería observar el siguiente resultado en la terminal:


### 9. Borrar las tareas pendientes de Celery
Por último, se deben borrar las tareas encoladas en Celery que se crearon durante las pruebas:
```bash
celery -A tasks purge --force
```

## SonarQube
El reporte de las pruebas de SonarQube se encuentra en [docs/Entrega_1/sonarqube.md](https://www.github.com/Laurarestrepo03/MISW4204-202515-GRUPO-7/docs/Entrega_1/sonarqube.md)