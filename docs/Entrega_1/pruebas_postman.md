## 👨‍🚀 Pruebas Postman
Antes de ejecutar las pruebas de Postman, se recomienda ver la documentación en línea:

**https://documenter.getpostman.com/view/17535481/2sB3QQK85r**

o importar localmente el archivo de la [colección ANB_Tests](../../collections/ANB_Tests.postman_collection.json) en Postman.

Una vez hecho esto, se deben seguir los siguientes pasos:

Nota: si ya ha hecho las instalaciones previas, salte al [paso 5](#5-iniciar-la-aplicación-uvicorn), y si ya está ejecutando la aplicación, salte al [paso 6](#6-parar-el-servicio-de-celery).

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

### 5. Iniciar la Aplicación Uvicorn
```bash
uvicorn main:app --reload
```

### 6. Parar el Servicio de Celery
Si tiene uno o varios servicios de Celery corriendo, termínelos **todos** en la terminal donde se estén ejecutando. Esto lo puede hacer con `ctrl+C` en Windows o `cmd+C` en Mac. 

Esto se hace con el fin de no procesar los videos subidos (2) durante las pruebas, puesto que pueden tardar un rato y ocupar el worker si se llega a necesitar de verdad. Si no le molesta y sí los quiere procesar, ignore este paso.

### 7. Asegurarse de Tener los Archivos Necesarios
Verifique que haya descargado la carpeta [assets](../../assets) de este mismo repositorio para tener los archivos de video.  

Si va a ejecutar las pruebas manualmente en Postman, es decir, si no va a seguir los pasos 8 a 10, es necesario que vaya a las pruebas que inician con el nombre "Subir video" y subir los archivos a su nube de Postman. Esto se puede hacer dando click en el ícono de nube al lado del archivo de video:

<a href="https://github.com/user-attachments/assets/d43535c5-7552-4e70-93b8-30bcbd015411"> <img width="833" height="142" alt="Subir pruebas a la nube" src="https://github.com/user-attachments/assets/d43535c5-7552-4e70-93b8-30bcbd015411" /> </a>

### 8. Asegurarse de Tener Newman Instalado
En una nueva terminal:
```bash
newman -v
```
Si no lo ha instalado, puede ejecutar este comando:
```bash
npm install -g newman
```
### 9. Correr las Pruebas
En una nueva terminal:
```bash
 newman run collections/ANB_Tests.postman_collection.json
```
### 10. Observar los Resultados
Una vez se hayan terminado de ejcutar las pruebas, debería observar el siguiente resultado en la terminal:

<a href="https://github.com/user-attachments/assets/dadb0ac3-6610-4f4d-a492-6be03a3806d4"> <img width="470" height="323" alt="Pruebas Postman ejecutadas" src="https://github.com/user-attachments/assets/dadb0ac3-6610-4f4d-a492-6be03a3806d4" /> </a>

Es importante notar que si se corren las pruebas más de una vez, a menos que se eliminen los usuarios correspondientes de la base de datos, las primeras dos pruebas de registro van a fallar, pues estas suponen que los usuarios no existen.

### 11. Borrar las tareas pendientes de Celery
Por último, se deben borrar las tareas encoladas en Celery que se crearon durante las pruebas:
```bash
celery -A tasks purge --force
```
