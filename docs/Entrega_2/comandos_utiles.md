## Comandos Útiles

### Activar un ambiente virtual

**En Windows:**
```bash
source venv/Scripts/activate
```

**En Linux/Mac/Ubuntu:**
```bash
source venv/bin/activate
```

### Limpiar las tareas pendientes de un worker
```bash
celery -A tasks purge --force
```