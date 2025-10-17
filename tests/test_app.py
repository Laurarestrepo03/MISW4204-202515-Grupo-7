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

def test_login_200():
    signup_body = signup()
    body = {"email": signup_body["email"], "password": signup_body["password1"]}
    response = client.post("/api/auth/login", json = body)
    assert response.status_code == 200
    assert response.json()["token_type"] is not None
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["expires_in"] == 3600


# Pruebas de gestion de videos
def test_upload_video_201():
    headers = get_headers()
    upload_body = generate_upload_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 201
    assert response.json()["message"] == "Video subido correctamente. Procesamiento en curso"
    assert response.json()["task_id"] is not None

def test_upload_video_401():
    upload_body = generate_upload_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", data=data, files=files)
    assert response.status_code == 401
    assert response.json() == {"detail": "Falta de autenticación."}

four_hundred_error = "Error en el archivo (tipo o tamaño inválido)."

def test_upload_video_400_invalid_type():
    headers = get_headers()
    upload_body = generate_upload_body("wrong_type")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 400
    assert response.json()["message"] == four_hundred_error

def test_upload_video_400_invalid_duration():
    headers = get_headers()

# Pruebas de votacion

# Pruebas de ranking

# Funciones auxiliares
def generate_signup_body():
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = faker.email()
    password = faker.word()
    if len(password) < 8:
        while len(password) < 8:
            password += password
    elif len(password) > 72:
        password = password[:71]
    city = faker.city()
    country = faker.country()
    body = {"first_name": first_name, "last_name": last_name, "email": email, "password1": password, "password2": password, "city": city, "country": country}
    return body
    
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

def generate_upload_body(type: str):
    title = faker.sentence()
    rand_video = random.randint(1,2)

    if type == "valid":
        if rand_video == 1:
            video_path = "assets/Larry Bird.mp4"
        else:
            video_path = "assets/Michael Jordan.mp4"
        video_type = "mp4"
    elif type == "wrong_type":
        if rand_video == 1:
            video_path = "assets/Larry Bird.mkv"
            video_type = "mkv"
        else:
            video_path = "assets/Michael Jordan.mov"
            video_type = "mov"
    elif type == "wrong_duration":
        pass

    data = {"title": title}
    files = {"video_file": ("test_video."+video_type, open(video_path, "rb"), "video/"+video_type)}
    return data, files
