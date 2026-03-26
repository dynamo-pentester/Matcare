DROP TABLE IF EXISTS baby_readings;
DROP TABLE IF EXISTS mother_readings;
DROP TABLE IF EXISTS babies;
DROP TABLE IF EXISTS mothers;

CREATE TABLE mothers (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    wallet_addr TEXT UNIQUE NOT NULL,
    mother_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE babies (
    id SERIAL PRIMARY KEY,
    baby_id INTEGER,
    mother_id INTEGER,
    baby_name TEXT,
    baby_dob DATE,
    baby_gender TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mother_readings (
    id SERIAL PRIMARY KEY,
    mother_id INTEGER,
    pulse FLOAT,
    spo2 FLOAT,
    bp FLOAT,
    temp FLOAT,
    glucose FLOAT,
    prediction TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE baby_readings (
    id SERIAL PRIMARY KEY,
    baby_id INTEGER,
    pulse FLOAT,
    spo2 FLOAT,
    bp FLOAT,
    temp FLOAT,
    glucose FLOAT,
    prediction TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);