# webova cast projektu Flappy Bird ve Flasku + API pro hru
import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
import mysql.connector.errors

WEB_SLOZKA = Path(__file__).resolve().parent
PROJEKT_SLOZKA = WEB_SLOZKA.parent
OBRAZKY_SLOZKA = PROJEKT_SLOZKA / "src" / "obrazky"
DIAGRAMY_SLOZKA = PROJEKT_SLOZKA / "docs" / "diagramy"

sys.path.insert(0, str(PROJEKT_SLOZKA))
import pripojeni

app = Flask(__name__, template_folder=str(WEB_SLOZKA), static_folder=str(WEB_SLOZKA / "static"))
app.secret_key = "flappy_secret_2026_chrapko"
app.permanent_session_lifetime = timedelta(days=7)

# tokeny prihlasenych hracu ze hry (token -> user_id)
active_tokens = {}

# achievementy podle poctu projetych trubek
ACHIEVEMENTY = [
    (20, "20 trubek", "20.png"),
    (50, "50 trubek", "50.png"),
    (60, "60 trubek", "60.png"),
    (100, "100 trubek", "100.png"),
]

ACH_OBRAZKY = {
    "20 trubek": "20.png",
    "50 trubek": "50.png",
    "60 trubek": "60.png",
    "100 trubek": "100.png",
}


# pripojeni k MySQL databazi pres pripojeni.py
def get_db():
    return mysql.connector.connect(
        host=pripojeni.HOST,
        user=pripojeni.USER,
        password=pripojeni.PASSWORD,
        database=pripojeni.DATABASE,
        use_pure=True,
        connection_timeout=3,
    )


# vytvoreni tabulek pri startu pokud neexistuji
def _init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                jmeno VARCHAR(50) NOT NULL UNIQUE,
                heslo VARCHAR(255) NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nastaveni (
                id INT PRIMARY KEY,
                key_binds VARCHAR(50) NOT NULL DEFAULT 'up',
                FOREIGN KEY (id) REFERENCES user(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hra (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                score INT NOT NULL DEFAULT 0,
                cas INT NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nazev VARCHAR(50) NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hra_tag (
                hra_id INT NOT NULL,
                tag_id INT NOT NULL,
                PRIMARY KEY (hra_id, tag_id),
                FOREIGN KEY (hra_id) REFERENCES hra(id),
                FOREIGN KEY (tag_id) REFERENCES tag(id)
            )
        """)
        for _, nazev, _ in ACHIEVEMENTY:
            cursor.execute("INSERT IGNORE INTO tag (nazev) VALUES (%s)", (nazev,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass


_init_db()


# hlavni stranka
@app.route("/")
@app.route("/index.html")
def home():
    moje_hry = []
    if session.get("user_id"):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT h.score, h.cas,
                       GROUP_CONCAT(t.nazev ORDER BY t.id SEPARATOR ', ') AS tagy
                FROM hra h
                LEFT JOIN hra_tag ht ON h.id = ht.hra_id
                LEFT JOIN tag t ON ht.tag_id = t.id
                WHERE h.user_id = %s
                GROUP BY h.id, h.score, h.cas
                ORDER BY h.id DESC
                LIMIT 5
            """, (session["user_id"],))
            moje_hry = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            pass
    return render_template(
        "index.html",
        hrac=session.get("username"),
        moje_hry=moje_hry,
        ach_obrazky=ACH_OBRAZKY,
    )


# registrace noveho uzivatele
@app.route("/registrace", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
@app.route("/registrace.html", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            error = "Zadej jmeno i heslo."
        else:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user (jmeno, heslo) VALUES (%s, %s)",
                    (username, generate_password_hash(password, method="pbkdf2:sha256")),
                )
                user_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO nastaveni (id, key_binds) VALUES (%s, %s)",
                    (user_id, "up"),
                )
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for("login"))
            except mysql.connector.errors.IntegrityError:
                error = "Toto jmeno je jiz obsazeno."
            except mysql.connector.Error as e:
                error = f"Chyba databaze: {e}"
    return render_template("registrace.html", hrac=session.get("username"), error=error)


# prihlaseni uzivatele na webu
@app.route("/login", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, heslo FROM user WHERE jmeno = %s", (username,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row and check_password_hash(row[1], password):
                session.permanent = True
                session["user_id"] = row[0]
                session["username"] = username
                return redirect(url_for("home"))
            else:
                error = "Nespravne jmeno nebo heslo."
        except mysql.connector.Error as e:
            error = f"Chyba databaze: {e}"
    return render_template("login.html", hrac=session.get("username"), error=error)


# odhlaseni
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# leaderboard TOP 10 podle projetych trubek vcetne achievementu z toho runu
@app.route("/leaderboard")
@app.route("/leaderboard.html")
def leaderboard():
    scores = []
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.jmeno, h.score, h.cas,
                   GROUP_CONCAT(t.nazev ORDER BY t.id SEPARATOR ', ') AS tagy
            FROM hra h
            JOIN user u ON h.user_id = u.id
            LEFT JOIN hra_tag ht ON h.id = ht.hra_id
            LEFT JOIN tag t ON ht.tag_id = t.id
            GROUP BY h.id, u.jmeno, h.score, h.cas
            ORDER BY h.score DESC, h.cas ASC
            LIMIT 10
        """)
        scores = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception:
        scores = []

    return render_template(
        "leaderboard.html",
        hrac=session.get("username"),
        scores=scores,
        ach_obrazky=ACH_OBRAZKY,
    )


# stranka s pravidly
@app.route("/pravidla")
@app.route("/pravidla.html")
def pravidla():
    return render_template("pravidla.html", hrac=session.get("username"))


# stranka s ER diagramem
@app.route("/diagramy")
@app.route("/diagramy.html")
def diagramy():
    return render_template("diagramy.html", hrac=session.get("username"))


# obrazek ER diagramu
@app.route("/er-diagram")
def er_diagram():
    return send_from_directory(DIAGRAMY_SLOZKA, "ER diagram.png")


# PNG obrazky achievementu (20, 50, 60, 100)
@app.route("/obrazek/<nazev>")
def obrazek_achievementu(nazev):
    if nazev in ("20.png", "50.png", "60.png", "100.png"):
        return send_from_directory(OBRAZKY_SLOZKA, nazev)
    return "Nenalezeno", 404


# API pro prihlaseni ze hry (vraci token + ulozenou klavesu)
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT u.id, u.heslo, n.key_binds "
            "FROM user u LEFT JOIN nastaveni n ON u.id = n.id "
            "WHERE u.jmeno = %s",
            (username,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and check_password_hash(row[1], password):
            token = secrets.token_hex(16)
            active_tokens[token] = row[0]
            key_binds = row[2] if row[2] else "up"
            return jsonify({
                "success": True,
                "token": token,
                "username": username,
                "key_binds": key_binds,
            })
        return jsonify({"success": False, "error": "Nespravne jmeno nebo heslo."})
    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Chyba databaze: {e}"})


# API pro ulozeni skore, casu a ziskanych achievementu ze hry
@app.route("/api/score", methods=["POST"])
def api_score():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    score = int(data.get("score", 0))
    cas = int(data.get("cas", 1))
    user_id = active_tokens.get(token)
    if not user_id:
        return jsonify({"success": False, "error": "Neplatny token."})
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hra (user_id, score, cas) VALUES (%s, %s, %s)",
            (user_id, score, cas),
        )
        hra_id = cursor.lastrowid

        # automaticky zapis ziskanych achievementu (20, 50, 60, 100 trubek)
        for limit, nazev, _ in ACHIEVEMENTY:
            if score >= limit:
                cursor.execute("INSERT IGNORE INTO tag (nazev) VALUES (%s)", (nazev,))
                cursor.execute("SELECT id FROM tag WHERE nazev = %s", (nazev,))
                tag_row = cursor.fetchone()
                if tag_row:
                    cursor.execute(
                        "INSERT IGNORE INTO hra_tag (hra_id, tag_id) VALUES (%s, %s)",
                        (hra_id, tag_row[0]),
                    )

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Chyba databaze: {e}"})


# API pro ulozeni klavesy z Settings ve hre
@app.route("/api/keybind", methods=["POST"])
def api_keybind():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    key_binds = str(data.get("key_binds", "up"))[:50]
    user_id = active_tokens.get(token)
    if not user_id:
        return jsonify({"success": False, "error": "Neplatny token."})
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO nastaveni (id, key_binds) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE key_binds = %s",
            (user_id, key_binds, key_binds),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Chyba databaze: {e}"})


if __name__ == "__main__":
    app.run()
