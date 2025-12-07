CREATE TABLE IF NOT EXISTS ml_user (
    email VARCHAR(255) PRIMARY KEY,
    pwd TEXT NOT NULL,
    tokens INT DEFAULT 15
);

CREATE TABLE IF NOT EXISTS ml_models (
    model_name VARCHAR(255) PRIMARY KEY,
    owner_email VARCHAR(255) REFERENCES ml_user(email) ON DELETE CASCADE,
    algorithm VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_logs (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) REFERENCES ml_user(email) ON DELETE SET NULL,
    action VARCHAR(255),
    model_name VARCHAR(255),
    timestamp TIMESTAMP DEFAULT NOW()
);
