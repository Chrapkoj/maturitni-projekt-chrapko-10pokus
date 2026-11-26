# hlavni menu, login obrazovka, nastaveni klaves a automaticky start Flask webu
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import urllib.request
import webbrowser
import pygame
from game import SERVER_URL, spust_hru


# spusti Flask server na pozadi
def spust_web_server():
    projekt_slozka = Path(__file__).resolve().parent.parent
    web_cesta = projekt_slozka / "web" / "app.py"
    pripojeni_cesta = projekt_slozka / "pripojeni.py"

    if not web_cesta.exists():
        print("[WEB] CHYBA: web/app.py nenalezen")
        return None, None
    if not pripojeni_cesta.exists():
        print("[WEB] CHYBA: pripojeni.py nenalezen! Zkopiruj pripojeni.example.py jako pripojeni.py")
        return None, None

    log_cesta = projekt_slozka / "flask.log"
    log_soubor = open(log_cesta, "w")
    proces = subprocess.Popen(
        [sys.executable, str(web_cesta)],
        stdout=log_soubor,
        stderr=log_soubor,
    )
    print(f"[WEB] Flask server spusten (PID {proces.pid})")
    return proces, log_soubor


# odeslani zmenene klavesy na Flask /api/keybind
def posli_keybind_api(token, key_name):
    def _vlakno():
        try:
            telo = json.dumps({"token": token, "key_binds": key_name}).encode("utf-8")
            req = urllib.request.Request(
                f"{SERVER_URL}/api/keybind",
                data=telo,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5).close()
        except Exception:
            pass

    threading.Thread(target=_vlakno, daemon=True).start()


def spust_menu():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

    # spusteni Flask serveru na pozadi pri startu hry
    web_proces, flask_log = spust_web_server()

    # cesta k obrazkum a fontu
    image_folder = Path(__file__).resolve().parent / "obrazky"
    font_path = image_folder / "flappy-font.ttf"

    # pozadi a tlacitka menu
    background_night = pygame.transform.smoothscale(
        pygame.image.load(image_folder / "background-night.png").convert(), (800, 600)
    )
    start_image = pygame.transform.smoothscale(
        pygame.image.load(image_folder / "start.png").convert_alpha(), (260, 82)
    )
    settings_image = pygame.transform.smoothscale(
        pygame.image.load(image_folder / "settings.jpg").convert_alpha(), (260, 85)
    )
    exit_image = pygame.transform.smoothscale(
        pygame.image.load(image_folder / "exit.png").convert_alpha(), (260, 89)
    )

    # pozice tlacitek
    start_button = start_image.get_rect(center=(400, 235))
    settings_button = settings_image.get_rect(center=(400, 335))
    exit_button = exit_image.get_rect(center=(400, 435))
    settings_header = settings_image.get_rect(center=(400, 130))

    # fonty
    title_font = pygame.font.Font(font_path, 52)
    title = title_font.render("FLAPPY BIRD", True, (255, 255, 255))
    settings_font = pygame.font.Font(font_path, 32)
    back_font = pygame.font.Font(font_path, 34)
    small_font = pygame.font.Font(font_path, 20)

    back_text = back_font.render("BACK (ESC)", True, (255, 255, 255))
    back_button = back_text.get_rect(center=(400, 515))

    # stav klavesy a prihlaseni pres token z Flask API
    fly_up_key = pygame.K_UP
    waiting_for_key = False
    auth_token = None
    jmeno_hrace = "HOST"

    # stav login obrazovky (stejny princip jako login_screen.py)
    login_jmeno = ""
    login_heslo = ""
    aktivni_pole = "jmeno"
    login_stav = {"zprava": "", "barva": (255, 110, 110), "loading": False, "vysledek": None}

    box_jmeno = pygame.Rect(220, 215, 360, 45)
    box_heslo = pygame.Rect(220, 305, 360, 45)
    btn_login = pygame.Rect(220, 385, 170, 48)
    btn_reg = pygame.Rect(410, 385, 170, 48)

    # pomocna funkce pro prihlaseni na pozadi pres /api/login
    def odesli_login():
        if login_stav["loading"]:
            return
        if login_jmeno.strip() == "" or login_heslo == "":
            login_stav["zprava"] = "ZADEJ JMENO I HESLO"
            login_stav["barva"] = (255, 110, 110)
            return

        login_stav["loading"] = True
        login_stav["zprava"] = "PRIHLASOVANI..."
        login_stav["barva"] = (220, 220, 220)

        def _vlakno():
            try:
                telo = json.dumps({"username": login_jmeno.strip(), "password": login_heslo}).encode("utf-8")
                req = urllib.request.Request(
                    f"{SERVER_URL}/api/login",
                    data=telo,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    login_stav["vysledek"] = data
                else:
                    login_stav["zprava"] = "SPATNE JMENO NEBO HESLO"
                    login_stav["barva"] = (255, 110, 110)
            except Exception:
                login_stav["zprava"] = "SERVER NENI DOSTUPNY"
                login_stav["barva"] = (255, 110, 110)
            finally:
                login_stav["loading"] = False

        threading.Thread(target=_vlakno, daemon=True).start()

    # hra zacina na login obrazovce
    stav = "login"

    run = True
    while run:
        clock.tick(60)

        # kontrola jestli dobehlo prihlaseni z vlakna
        if login_stav["vysledek"] is not None:
            data = login_stav["vysledek"]
            login_stav["vysledek"] = None
            auth_token = data["token"]
            jmeno_hrace = data.get("username", login_jmeno.strip())
            try:
                fly_up_key = pygame.key.key_code(data.get("key_binds", "up"))
            except ValueError:
                fly_up_key = pygame.K_UP
            login_heslo = ""
            login_stav["zprava"] = ""
            stav = "menu"

        # texty v settings
        if waiting_for_key:
            bind_label = "FLY UP = PRESS ANY KEY..."
            bind_color = (255, 220, 0)
        else:
            key_name = pygame.key.name(fly_up_key).upper()
            bind_label = "FLY UP = " + key_name
            bind_color = (255, 255, 255)

        bind_text = settings_font.render(bind_label, True, bind_color)
        bind_button = bind_text.get_rect(center=(400, 300))

        # spodni tlacitka v menu (web + odhlaseni/login)
        web_surf = small_font.render("OTEVRIT WEB", True, (130, 210, 255))
        web_rect = web_surf.get_rect(center=(280, 535))

        auth_txt = "ODHLASIT (" + jmeno_hrace.upper() + ")" if auth_token else "PRIHLASIT SE"
        auth_surf = small_font.render(auth_txt, True, (255, 220, 0))
        auth_rect = auth_surf.get_rect(center=(520, 535))

        # preskoceni loginu (kdyz neni zapla DB)
        skip_surf = small_font.render("HRAT BEZ PRIHLASENI", True, (190, 200, 220))
        skip_rect = skip_surf.get_rect(center=(400, 520))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.KEYDOWN:
                if stav == "login":
                    if event.key == pygame.K_TAB:
                        aktivni_pole = "heslo" if aktivni_pole == "jmeno" else "jmeno"
                    elif event.key == pygame.K_RETURN:
                        odesli_login()
                    elif event.key == pygame.K_BACKSPACE:
                        if aktivni_pole == "jmeno":
                            login_jmeno = login_jmeno[:-1]
                        else:
                            login_heslo = login_heslo[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        if aktivni_pole == "jmeno" and len(login_jmeno) < 30:
                            login_jmeno += event.unicode
                        elif aktivni_pole == "heslo" and len(login_heslo) < 50:
                            login_heslo += event.unicode

                elif stav == "settings":
                    if waiting_for_key:
                        if event.key != pygame.K_ESCAPE:
                            fly_up_key = event.key
                            if auth_token:
                                posli_keybind_api(auth_token, pygame.key.name(fly_up_key))
                        waiting_for_key = False
                    elif event.key == pygame.K_ESCAPE:
                        stav = "menu"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if stav == "login":
                    if box_jmeno.collidepoint(event.pos):
                        aktivni_pole = "jmeno"
                    elif box_heslo.collidepoint(event.pos):
                        aktivni_pole = "heslo"
                    elif btn_login.collidepoint(event.pos):
                        odesli_login()
                    elif btn_reg.collidepoint(event.pos):
                        webbrowser.open(f"{SERVER_URL}/registrace")
                    elif skip_rect.collidepoint(event.pos):
                        auth_token = None
                        jmeno_hrace = "HOST"
                        stav = "menu"

                elif stav == "menu":
                    if start_button.collidepoint(event.pos):
                        vysledek = spust_hru(screen, fly_up_key, auth_token, jmeno_hrace)
                        if vysledek == "quit":
                            run = False
                    elif settings_button.collidepoint(event.pos):
                        stav = "settings"
                    elif exit_button.collidepoint(event.pos):
                        run = False
                    elif web_rect.collidepoint(event.pos):
                        webbrowser.open(SERVER_URL)
                    elif auth_rect.collidepoint(event.pos):
                        auth_token = None
                        jmeno_hrace = "HOST"
                        fly_up_key = pygame.K_UP
                        login_stav["zprava"] = ""
                        stav = "login"

                elif stav == "settings":
                    if bind_button.collidepoint(event.pos):
                        waiting_for_key = True
                    elif back_button.collidepoint(event.pos):
                        waiting_for_key = False
                        stav = "menu"

        # vykresleni obrazovky
        screen.blit(background_night, (0, 0))

        if stav == "login":
            screen.blit(title, title.get_rect(center=(400, 105)))
            sub = small_font.render("-- LOGIN --", True, (255, 220, 0))
            screen.blit(sub, sub.get_rect(center=(400, 155)))

            screen.blit(small_font.render("USERNAME:", True, (255, 255, 255)), (220, 188))
            screen.blit(small_font.render("PASSWORD:", True, (255, 255, 255)), (220, 278))

            barva_j = (255, 215, 0) if aktivni_pole == "jmeno" else (140, 150, 170)
            barva_h = (255, 215, 0) if aktivni_pole == "heslo" else (140, 150, 170)

            pygame.draw.rect(screen, (15, 20, 35), box_jmeno)
            pygame.draw.rect(screen, barva_j, box_jmeno, 2)
            pygame.draw.rect(screen, (15, 20, 35), box_heslo)
            pygame.draw.rect(screen, barva_h, box_heslo, 2)

            screen.blit(small_font.render(login_jmeno, True, (255, 255, 255)), (230, 227))
            screen.blit(small_font.render("*" * len(login_heslo), True, (255, 255, 255)), (230, 317))

            pygame.draw.rect(screen, (45, 145, 75), btn_login)
            pygame.draw.rect(screen, (50, 95, 165), btn_reg)
            t_log = small_font.render("LOGIN", True, (255, 255, 255))
            t_reg = small_font.render("REGISTER", True, (255, 255, 255))
            screen.blit(t_log, t_log.get_rect(center=btn_login.center))
            screen.blit(t_reg, t_reg.get_rect(center=btn_reg.center))

            if login_stav["zprava"] != "":
                msg = small_font.render(login_stav["zprava"], True, login_stav["barva"])
                screen.blit(msg, msg.get_rect(center=(400, 468)))

            screen.blit(skip_surf, skip_rect)

        elif stav == "menu":
            screen.blit(title, title.get_rect(center=(400, 120)))
            screen.blit(start_image, start_button)
            screen.blit(settings_image, settings_button)
            screen.blit(exit_image, exit_button)
            screen.blit(web_surf, web_rect)
            screen.blit(auth_surf, auth_rect)

        elif stav == "settings":
            screen.blit(settings_image, settings_header)
            screen.blit(bind_text, bind_button)
            screen.blit(back_text, back_button)

        pygame.display.flip()

    # ukonceni Flask serveru na pozadi pri zavreni hry
    if web_proces is not None and web_proces.poll() is None:
        web_proces.terminate()
    if flask_log is not None:
        flask_log.close()
    pygame.quit()


if __name__ == "__main__":
    spust_menu()
