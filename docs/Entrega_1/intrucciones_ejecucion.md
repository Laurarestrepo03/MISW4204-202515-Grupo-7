## 🚀 Pasos para Ejecutar la Aplicación

### 1. Crear el Ambiente Virtual
```bash
python -m venv venv
```

### 2. Activar el Ambiente Virtual
**En Windows:**
```bash
source venv\Scripts\activate
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

### 5. Iniciar el Servicio de Celery
**IMPORTANTE:** Este paso debe ejecutarse ANTES de correr la aplicación Uvicorn. Los videos que se intenten procesar sin tener Celery corriendo no se procesarán.

```bash
celery -A tasks worker -l info -P solo
```

### 6. Iniciar la Aplicación Uvicorn
En una nueva terminal (manteniendo Celery corriendo):
```bash
uvicorn main:app --reload
```

### 7. Usar la Aplicación
Para una demostración de cómo usar la aplicación, recomendamos ver el video en [sustentacion/Entrega_1.md](../../sustentacion/Entrega_1.md), minuto [00:00]().