from fastapi.testclient import TestClient
from faker import Faker
from main import app
from database import SessionLocal
from sqlalchemy import delete
import models
import random

client = TestClient(app)
faker = Faker()

# Error vars
upload_400_hundred_error = "Error en el archivo (tipo, duración o tamaño inválido)."
signup_400_error = {"detail": "Error de validación (email duplicado, contraseñas no coinciden)."}
login_401_error = {"detail": "Credenciales inválidas."}
auth_error = {"detail": "Falta de autenticación."}
video_404_error = {"detail":"El video con el video_id especificado no existe"}

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
    delete_user(body["email"])

def test_signup_400_invalid_email():
    body = generate_signup_body()
    client.post("/api/auth/signup", json=body)
    response = client.post("/api/auth/signup", json=body)
    assert response.status_code == 400
    assert response.json() == signup_400_error
    delete_user(body["email"])

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
    delete_user(signup_body["email"])

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
    delete_user(signup_body["email"])

# Pruebas de gestion de videos
def test_upload_video_201():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 201
    assert response.json()["message"] == "Video subido correctamente. Procesamiento en curso"
    assert response.json()["task_id"] is not None
    delete_video(response.json()["task_id"])
    delete_user(signup_body["email"])

def test_upload_video_401():
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", data=data, files=files)
    assert response.status_code == 401
    assert response.json() == auth_error

def test_upload_video_400_invalid_type():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("wrong_type")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 400
    assert response.json()["message"] == upload_400_hundred_error
    delete_user(signup_body["email"])

def test_upload_video_400_invalid_duration():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("wrong_duration")
    data = upload_body[0]
    files = upload_body[1]
    response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    assert response.status_code == 400
    assert response.json()["message"] == upload_400_hundred_error
    delete_user(signup_body["email"])


# def test_upload_video_400_invalid_size():
#     signup_body = signup()
#     token = login(signup_body)
#     headers = get_headers(token)
#     upload_body = generate_video_body("wrong_size")
#     data = upload_body[0]
#     files = upload_body[1]
#     response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
#     assert response.status_code == 400
#     assert response.json()["message"] == upload_400_hundred_error
#     delete_user(signup_body["email"])

def test_get_videos_200():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    response = client.get("/api/videos", headers=headers)
    assert response.status_code == 200
    assert "videos" in response.json()
    assert "total" in response.json()
    assert response.json()["total"] >= 1
    delete_video(upload_response.json()["task_id"])
    delete_user(signup_body["email"])

def test_get_videos_200():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    video1_body = generate_video_body("valid")
    video1_data = video1_body[0]
    video1_files = video1_body[1]
    video1_response = client.post("/api/videos/upload", headers=headers, data=video1_data, files=video1_files)
    video2_body = generate_video_body("valid")
    video2_data = video2_body[0]
    video2_files = video2_body[1]
    video2_response = client.post("/api/videos/upload", headers=headers, data=video2_data, files=video2_files)
    response = client.get("/api/videos", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    delete_video(video1_response.json()["task_id"])
    delete_video(video2_response.json()["task_id"])
    delete_user(signup_body["email"])

def test_get_videos_401():
    response = client.get("/api/videos")
    assert response.status_code == 401
    assert response.json() == auth_error

def test_get_video_200():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    task_id = upload_response.json()["task_id"]
    video_id = get_video_id(task_id)
    response = client.get("api/videos/"+str(video_id), headers=headers)
    assert response.status_code == 200
    assert response.json()["video_id"] == video_id
    delete_video(task_id)
    delete_user(signup_body["email"])

def test_get_video_401():
    video_id = random.randint(1,999)
    response = client.get("api/videos/"+str(video_id))
    assert response.status_code == 401
    assert response.json() == auth_error

def test_get_video_403():
    user1_signup_body = signup()
    user1_token = login(user1_signup_body)
    user1_headers = get_headers(user1_token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=user1_headers, data=data, files=files)
    task_id = upload_response.json()["task_id"]
    video_id = get_video_id(task_id)
    user2_signup_body = signup()
    user2_token = login(user2_signup_body)
    user2_headers = get_headers(user2_token)
    response = client.get("api/videos/"+str(video_id), headers=user2_headers)
    assert response.status_code == 403
    assert response.json() == {"detail":"No tienes permiso para acceder a este video"}
    delete_video(task_id)
    delete_user(user1_signup_body["email"])
    delete_user(user2_signup_body["email"])

def test_get_video_404():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    task_id = upload_response.json()["task_id"]
    video_id = get_video_id(task_id)
    delete_video(task_id)
    response = client.get("api/videos/"+str(video_id), headers=headers)
    assert response.status_code == 404
    assert response.json() == video_404_error
    delete_user(signup_body["email"])

def test_delete_video_200():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    task_id = upload_response.json()["task_id"]
    video_id = get_video_id(task_id)
    response = client.delete("api/videos/"+str(video_id), headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message":"Video eliminado exitosamente", "video_id": video_id}
    assert get_video_id(task_id) == 0
    delete_user(signup_body["email"])

"""def test_delete_video_400():
    pass"""

def test_delete_video_401():
    video_id = random.randint(1,999)
    response = client.delete("api/videos/"+str(video_id))
    assert response.status_code == 401
    assert response.json() == auth_error

def test_delete_video_403():
    user1_signup_body = signup()
    user1_token = login(user1_signup_body)
    user1_headers = get_headers(user1_token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=user1_headers, data=data, files=files)
    task_id = upload_response.json()["task_id"]
    video_id = get_video_id(task_id)
    user2_signup_body = signup()
    user2_token = login(user2_signup_body)
    user2_headers = get_headers(user2_token)
    response = client.delete("api/videos/"+str(video_id), headers=user2_headers)
    assert response.status_code == 403
    assert response.json() == {"detail":"No tienes permiso para eliminar este video"}
    delete_video(task_id)
    delete_user(user1_signup_body["email"])
    delete_user(user2_signup_body["email"])

def test_delete_video_404():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    task_id = upload_response.json()["task_id"]
    video_id = get_video_id(task_id)
    delete_video(task_id)
    response = client.delete("api/videos/"+str(video_id), headers=headers)
    assert response.status_code == 404
    assert response.json() == video_404_error
    delete_user(signup_body["email"])

# Pruebas de votacion
def test_vote_video_200():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    video_id = get_video_id(upload_response.json()["task_id"])
    
    signup_body2 = signup()
    token2 = login(signup_body2)
    headers2 = get_headers(token2)
    
    response = client.post(f"/api/public/videos/{video_id}/vote", headers=headers2)
    assert response.status_code == 200
    assert response.json()["message"] == "Voto registrado exitosamente."
    delete_vote(video_id, signup_body2["email"])
    delete_video(upload_response.json()["task_id"])
    delete_user(signup_body["email"])
    delete_user(signup_body2["email"])

def test_vote_video_400():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    upload_body = generate_video_body("valid")
    data = upload_body[0]
    files = upload_body[1]
    upload_response = client.post("/api/videos/upload", headers=headers, data=data, files=files)
    video_id = get_video_id(upload_response.json()["task_id"])
    
    signup_body2 = signup()
    token2 = login(signup_body2)
    headers2 = get_headers(token2)
    
    client.post(f"/api/public/videos/{video_id}/vote", headers=headers2)
    response = client.post(f"/api/public/videos/{video_id}/vote", headers=headers2)
    assert response.status_code == 400
    assert response.json() == {"detail": "Ya has votado por este video"}
    delete_vote(video_id, signup_body2["email"])
    delete_video(upload_response.json()["task_id"])
    delete_user(signup_body["email"])
    delete_user(signup_body2["email"])

def test_vote_video_404():
    signup_body = signup()
    token = login(signup_body)
    headers = get_headers(token)
    invalid_video_id = 999999
    response = client.post(f"/api/public/videos/{invalid_video_id}/vote", headers=headers)
    assert response.status_code == 404
    assert response.json() == video_404_error
    delete_user(signup_body["email"])

def test_vote_video_401():
    response = client.post("/api/public/videos/1/vote")
    assert response.status_code == 401
    assert response.json() == auth_error

# Pruebas de ranking
def test_get_ranking_200():
    response = client.get("/api/public/ranking")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_ranking_200_with_filters():
    signup_body = signup()
    city = signup_body["city"]
    first_name = signup_body["first_name"]
    response = client.get(f"/api/public/ranking?city={city}&name={first_name}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    delete_user(signup_body["email"])

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

def login(body: dict):
    login_body = {"email": body["email"], "password": body["password1"]}
    response = client.post("/api/auth/login", json = login_body)
    token = response.json()["access_token"]
    return token

def get_headers(token: str): 
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

def delete_user(email: str):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email).first()
        if not user:
            pass
        else:
            db.delete(user)
            db.commit()    
    finally:
        db.close()

def delete_video(task_id: str):
    db = SessionLocal()
    try:
        video = db.query(models.Video).filter_by(task_id=task_id).first()
        if not video:
            pass
        else:
            db.delete(video)
            db.commit()    
    finally:
        db.close()

def get_video_id(task_id: str):
    db = SessionLocal()
    try:
        video = db.query(models.Video).filter_by(task_id=task_id).first()
        if not video:
            return 0
        else:
            video_id = video.video_id 
            return video_id  
    finally:
        db.close()

def delete_vote(video_id: int, email: str):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email).first()
        if not user:
            pass
        else:
            vote = db.query(models.Vote).filter_by(video_id=video_id, user_id=user.user_id).first()
            if vote:
                db.delete(vote)
                db.commit()
    finally:
        db.close()