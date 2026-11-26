# skript pro vytvoreni tabulek a zakladnich achievementu v MySQL databazi
import os
import sys
import mysql.connector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pripojeni

try:
    conn = mysql.connector.connect(
        host=pripojeni.HOST,
        user=pripojeni.USER,
        password=pripojeni.PASSWORD,
        database=pripojeni.DATABASE,
        use_pure=True,
    )
    cursor = conn.cursor()

    # tabulka uzivatelu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            jmeno VARCHAR(50) NOT NULL UNIQUE,
            heslo VARCHAR(255) NOT NULL
        )
    """)

    # tabulka nastaveni klaves (1:1 s user)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nastaveni (
            id INT PRIMARY KEY,
            key_binds VARCHAR(50) NOT NULL DEFAULT 'up',
            FOREIGN KEY (id) REFERENCES user(id)
        )
    """)

    # tabulka odehranych her (1:N s user)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hra (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            score INT NOT NULL DEFAULT 0,
            cas INT NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    """)

    # tabulka tagu = achievementy za 20, 50, 60 a 100 trubek
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tag (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nazev VARCHAR(50) NOT NULL UNIQUE
        )
    """)

    # spojovaci tabulka hra <-> tag (M:N)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hra_tag (
            hra_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (hra_id, tag_id),
            FOREIGN KEY (hra_id) REFERENCES hra(id),
            FOREIGN KEY (tag_id) REFERENCES tag(id)
        )
    """)

    # vlozeni 4 zakladnich achievementu
    for nazev in ("20 trubek", "50 trubek", "60 trubek", "100 trubek"):
        cursor.execute("INSERT IGNORE INTO tag (nazev) VALUES (%s)", (nazev,))

    conn.commit()
    cursor.close()
    conn.close()
    print("Tabulky user, nastaveni, hra, tag a hra_tag jsou v poradku.")
except mysql.connector.Error as e:
    print(f"Chyba pri pripojeni k databazi: {e}")
