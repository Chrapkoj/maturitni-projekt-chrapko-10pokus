-- vytvoreni databaze
CREATE DATABASE IF NOT EXISTS flappy;

USE flappy;

-- tabulka user (Id, Jmeno, Heslo)
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jmeno VARCHAR(50) NOT NULL UNIQUE,
    heslo VARCHAR(255) NOT NULL
);

-- tabulka pro nastaveni (Id, Key binds)
CREATE TABLE IF NOT EXISTS nastaveni (
    id INT PRIMARY KEY,
    key_binds VARCHAR(50) NOT NULL DEFAULT 'up',
    FOREIGN KEY (id) REFERENCES user(id)
);

-- tabulka pro hru (Id, Score, Cas)
CREATE TABLE IF NOT EXISTS hra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    cas INT NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- tabulka tag (slouzi jako achievementy za 20, 50, 60 a 100 trubek)
CREATE TABLE IF NOT EXISTS tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nazev VARCHAR(50) NOT NULL UNIQUE
);

-- spojovaci tabulka pro hru a tagy (achievementy)
CREATE TABLE IF NOT EXISTS hra_tag (
    hra_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (hra_id, tag_id),
    FOREIGN KEY (hra_id) REFERENCES hra(id),
    FOREIGN KEY (tag_id) REFERENCES tag(id)
);
