-- Script de inicialización para la base de datos ANB
-- Este archivo se ejecuta automáticamente cuando se crea el contenedor

-- Crear tabla users
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla videos con el modelo actualizado
CREATE TABLE IF NOT EXISTS videos (
    video_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'uploaded',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    original_url TEXT,
    processed_url TEXT,
    votes INTEGER DEFAULT 0,
    task_id VARCHAR(255),
    user_id INTEGER NOT NULL,
    player_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_title ON videos(title);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_uploaded_at ON videos(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);

-- Insertar algunos datos de ejemplo (opcional)
-- INSERT INTO users (first_name, last_name, email, hashed_password, city, country) VALUES 
-- ('Juan', 'Pérez', 'juan@example.com', '$2b$12$hashedpassword', 'Bogotá', 'Colombia');

-- INSERT INTO videos (title, status, uploaded_at, original_url, votes, user_id) VALUES 
-- ('Video de ejemplo 1', 'uploaded', NOW(), 'https://example.com/video1.mp4', 0, 1),
-- ('Video de ejemplo 2', 'processed', NOW(), 'https://example.com/video2.mp4', 5, 1);
