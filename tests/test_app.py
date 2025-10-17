from fastapi.testclient import TestClient
from faker import Faker
from main import app
import random

client = TestClient(app)
faker = Faker()

"""def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}"""

# Pruebas de gestion de usuarios
def test_signup_201():
    body = generate_signup_body()
    user = {"first_name": body["first_name"], "last_name": body["last_name"], "email": body["email"], "city": body["city"], "country": body["country"]}
    response = client.post("/api/auth/signup", json=body)
    assert response.status_code == 201
    assert response.json() == {"message": "Usuario creado exitosamente.", "user": user}

signup_400_error = {"detail": "Error de validación (email duplicado, contraseñas no coinciden)."}

def test_signup_400_invalid_email():
    body = generate_signup_body()
    client.post("/api/auth/signup", json=body)
    response = client.post("/api/auth/signup", json=body)
    assert response.status_code == 400
    assert response.json() == signup_400_error

def test_signup_400_invalid_password():
    body = generate_signup_body(valid_password=False)
    response = client.post("/api/auth/signup", json=body)
    assert response.status_code == 400
    assert response.json() == signup_400_error
    
def test_login_200():
    signup_body = signup()
    body = {"email": signup_body["email"], "password": signup_body["password1"]}
    response = client.post("/api/auth/login", json = body)
    assert response.status_code == 200
    assert response.json()["token_type"] is not None
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["expires_in"] == 3600

login_401_error = {"detail": "Credenciales inválidas."}

def test_login_401_invalid_email():
    invalid_email = faker.email()
    password = faker.word()
    password = regenerate_password(password)
    body = {"email": invalid_email, "password": password}
    response = client.post("/api/auth/login", json = body)
    assert response.status_code == 401
    assert response.json() == login_401_error

def test_login_401_invalid_password():
    signup_body = signup()
    valid_password = signup_body["password1"]
    invalid_password = faker.word()
    invalid_password = regenerate_password(invalid_password)
    while invalid_password == valid_password:
        invalid_password = faker.word()
        invalid_password = regenerate_password(invalid_password)
    body = {"email": signup_body["email"], "password": invalid_password} 
    response = client.post("/api/auth/login", json = body)
    assert response.status_code == 401
    assert response.json() == login_401_error

# Pruebas de gestion de videos
def test_upload_video_201():
    headers = get_headers()
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 201
    assert response.json()["message"] == "Video subido correctamente. Procesamiento en curso"
    assert response.json()["task_id"] is not None

def test_upload_video_401():
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", data=data, files=files)
    assert response.status_code == 401
    assert response.json() == {"detail": "Falta de autenticación."}

upload_400_hundred_error = "Error en el archivo (tipo, duración o tamaño inválido)."

def test_upload_video_400_invalid_type():
    headers = get_headers()
    upload_body = generate_video_body("wrong_type")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 400
    assert response.json()["message"] == upload_400_hundred_error

def test_upload_video_400_invalid_duration():
    headers = get_headers()
    upload_body = generate_video_body("wrong_duration")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 400
    assert response.json()["message"] == upload_400_hundred_error

def test_upload_video_400_invalid_size():
    headers = get_headers()
    upload_body = generate_video_body("wrong_size")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 400
    assert response.json()["message"] == upload_400_hundred_error

# Pruebas de votacion

# Pruebas de ranking

# Funciones auxiliares
def generate_signup_body(valid_password=True):
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = faker.email()
    password = faker.word()
    password = regenerate_password(password)
    password1 = password
    if valid_password:
        password2 = password
    else:
        password2 = faker.word()
        password2 = regenerate_password(password2)
        while password2 == password1:
            password2 = faker.word()
            password2 = regenerate_password(password2)
    city = faker.city()
    country = faker.country()
    body = {"first_name": first_name, "last_name": last_name, "email": email, "password1": password1, "password2": password2, "city": city, "country": country}
    return body

def regenerate_password(password: str):
    if len(password) < 8:
        while len(password) < 8:
            password += password
    elif len(password) > 72:
        password = password[:71]
    return password
    
def signup():
    body = generate_signup_body()
    client.post("/api/auth/signup", json=body)
    return body

def get_headers(): 
    signup_body = signup()
    login_body = {"email": signup_body["email"], "password": signup_body["password1"]}
    response = client.post("/api/auth/login", json = login_body)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers

def generate_video_body(type: str):
    title = faker.sentence()
    rand_video = random.randint(1,2)
    video_type = "mp4"

    if type == "valid":
        if rand_video == 1:
            video_name = "Larry Bird.mp4"
        else:
            video_name = "Michael Jordan.mp4"
    elif type == "wrong_type":
        if rand_video == 1:
            video_name = "Larry Bird.mkv"
            video_type = "mkv"
        else:
            video_name = "Michael Jordan.mov"
            video_type = "mov"
    elif type == "wrong_duration":
        if rand_video == 1:
            video_name = "Short clip.mp4"
        else:
            video_name = "Long clip.mp4"
    elif type == "wrong_size":
        video_name = "Large size.mp4"

    video_path = "assets/" + video_name

    data = {"title": title}
    files = {"video_file": (video_name, open(video_path, "rb"), "video/"+video_type)}
    return data, files
