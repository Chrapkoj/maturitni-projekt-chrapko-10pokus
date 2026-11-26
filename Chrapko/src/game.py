# zakladni logika hry Flappy Bird + posilani skore pres Flask API
import json
from pathlib import Path
import random
import threading
import urllib.request
import pygame

# zakladni nastaveni okna a hry
SIRKA = 800
VYSKA = 600
ZEM_Y = 505
GRAVITACE = 0.45
SKOK = -8.5
RYCHLOST_TRUBEK = 4
MEZERA = 165
SERVER_URL = "http://localhost:5000"

# 4 achievementy za projete trubky
ACHIEVEMENTY = [
    (20, "20 trubek", "20.png"),
    (50, "50 trubek", "50.png"),
    (60, "60 trubek", "60.png"),
    (100, "100 trubek", "100.png"),
]


# vrati seznam ziskanych achievementu podle skore
def zjisti_achievementy(score):
    ziskane = []
    for limit, nazev, soubor in ACHIEVEMENTY:
        if score >= limit:
            ziskane.append((nazev, soubor))
    return ziskane


# odeslani skore a casu na Flask /api/score (ten ulozi i achievementy do DB)
def odesli_skore_api(token, score, cas, vysledek_box):
    def _vlakno():
        try:
            telo = json.dumps({"token": token, "score": score, "cas": cas}).encode("utf-8")
            req = urllib.request.Request(
                f"{SERVER_URL}/api/score",
                data=telo,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    vysledek_box["zprava"] = "SKORE ULOZENO DO DB"
                    vysledek_box["ok"] = True
                else:
                    vysledek_box["zprava"] = "CHYBA UKLADANI DO DB"
        except Exception:
            vysledek_box["zprava"] = "SERVER / DB NEDOSTUPNA"

    threading.Thread(target=_vlakno, daemon=True).start()


# spusteni samotne hry, vraci "menu" nebo "quit"
def spust_hru(screen, fly_up_key=pygame.K_UP, auth_token=None, jmeno_hrace="HOST"):
    clock = pygame.time.Clock()
    slozka = Path(__file__).resolve().parent / "obrazky"

    # nacteni obrazku hry
    pozadi = pygame.transform.smoothscale(
        pygame.image.load(slozka / "background-night.png").convert(), (SIRKA, VYSKA)
    )
    zem_obr = pygame.transform.smoothscale(
        pygame.image.load(slozka / "base.png").convert(), (340, VYSKA - ZEM_Y)
    )
    trubka_dole = pygame.transform.smoothscale(
        pygame.image.load(slozka / "pipe-green.png").convert_alpha(), (70, 450)
    )
    trubka_nahore = pygame.transform.flip(trubka_dole, False, True)

    ptak_obr = pygame.transform.smoothscale(
        pygame.image.load(slozka / "redbird-upflap.png").convert_alpha(), (50, 35)
    )

    # cisla pro vykresleni skore
    cisla = {}
    for i in range(10):
        obr = pygame.image.load(slozka / f"{i}.png").convert_alpha()
        cisla[str(i)] = pygame.transform.smoothscale(obr, (32, 48))

    gameover_obr = pygame.transform.smoothscale(
        pygame.image.load(slozka / "gameover.png").convert_alpha(), (300, 66)
    )
    gameover_panel_obr = pygame.transform.smoothscale(
        pygame.image.load(slozka / "gameover_panel.png").convert(), (480, 236)
    )

    # nacteni 4 PNG obrazku pro achievementy (20, 50, 60, 100 trubek)
    ach_obrazky = {}
    for _, nazev, soubor in ACHIEVEMENTY:
        ach_obrazky[nazev] = pygame.transform.smoothscale(
            pygame.image.load(slozka / soubor).convert_alpha(), (92, 92)
        )

    font_velky = pygame.font.Font(slozka / "flappy-font.ttf", 30)
    font_maly = pygame.font.Font(slozka / "flappy-font.ttf", 19)

    # promenne jednoho kola hry
    bird_x = 200
    bird_y = 250.0
    rychlost = 0.0
    zem_x = 0

    trubky = []
    timer_trubek = 0
    skore = 0
    cas_ms = 0
    hra_zacala = False
    game_over = False
    ulozene = False
    ziskane_ach = []
    stav_ulozeni = {"zprava": "", "ok": False}

    # reset vsech promennych pred novym kolem
    def reset_hry():
        nonlocal bird_y, rychlost, trubky, timer_trubek, skore, cas_ms
        nonlocal hra_zacala, game_over, ulozene, ziskane_ach, stav_ulozeni
        bird_y = 250.0
        rychlost = 0.0
        trubky = []
        timer_trubek = 45
        skore = 0
        cas_ms = 0
        hra_zacala = False
        game_over = False
        ulozene = False
        ziskane_ach = []
        stav_ulozeni = {"zprava": "", "ok": False}

    # konec kola -> zjisti achievementy a odesle vysledek pres Flask API
    def konec_kola():
        nonlocal game_over, ulozene, ziskane_ach
        game_over = True
        if ulozene:
            return
        ulozene = True

        ziskane_ach = zjisti_achievementy(skore)
        cas_s = max(1, cas_ms // 1000)

        if auth_token:
            stav_ulozeni["zprava"] = "UKLADAM DO DB..."
            odesli_skore_api(auth_token, skore, cas_s, stav_ulozeni)
        else:
            stav_ulozeni["zprava"] = "NEPRIHLASEN - SKORE NEULOZENO"

    reset_hry()

    # hlavni herni smycka
    while True:
        dt_ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_r, pygame.K_RETURN):
                    reset_hry()
                elif not game_over and event.key == fly_up_key:
                    hra_zacala = True
                    rychlost = SKOK

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    reset_hry()
                else:
                    hra_zacala = True
                    rychlost = SKOK

        # posun zeme
        if not game_over:
            zem_x -= RYCHLOST_TRUBEK
            if zem_x <= -340:
                zem_x = 0

        # pohyb ptaka a trubek
        if hra_zacala and not game_over:
            cas_ms += dt_ms
            rychlost += GRAVITACE
            if rychlost > 10:
                rychlost = 10
            bird_y += rychlost

            if bird_y < 20:
                bird_y = 20
                rychlost = 0

            timer_trubek += 1
            if timer_trubek >= 95:
                timer_trubek = 0
                mezera_y = random.randint(135, ZEM_Y - 135)
                trubky.append({"x": SIRKA + 50, "mezera_y": mezera_y, "projeta": False})

            ptak_rect = ptak_obr.get_rect(center=(bird_x, int(bird_y)))
            ptak_hitbox = ptak_rect.inflate(-10, -8)

            if ptak_hitbox.bottom >= ZEM_Y:
                bird_y = ZEM_Y - 18
                konec_kola()

            nove_trubky = []
            for t in trubky:
                t["x"] -= RYCHLOST_TRUBEK
                horni_rect = trubka_nahore.get_rect(midbottom=(t["x"], t["mezera_y"] - MEZERA // 2))
                dolni_rect = trubka_dole.get_rect(midtop=(t["x"], t["mezera_y"] + MEZERA // 2))

                if not t["projeta"] and t["x"] < bird_x:
                    t["projeta"] = True
                    skore += 1

                if ptak_hitbox.colliderect(horni_rect) or ptak_hitbox.colliderect(dolni_rect):
                    konec_kola()

                if t["x"] > -80:
                    nove_trubky.append(t)
            trubky = nove_trubky

        # vykresleni sceny
        screen.blit(pozadi, (0, 0))
        for t in trubky:
            horni_rect = trubka_nahore.get_rect(midbottom=(t["x"], t["mezera_y"] - MEZERA // 2))
            dolni_rect = trubka_dole.get_rect(midtop=(t["x"], t["mezera_y"] + MEZERA // 2))
            screen.blit(trubka_nahore, horni_rect)
            screen.blit(trubka_dole, dolni_rect)

        for gx in range(zem_x, SIRKA + 340, 340):
            screen.blit(zem_obr, (gx, ZEM_Y))

        screen.blit(ptak_obr, ptak_obr.get_rect(center=(bird_x, int(bird_y))))

        # vykresleni skore a info behem hry (na game over se nezobrazuje)
        if not game_over:
            skore_text = str(skore)
            celkova_sirka = len(skore_text) * 35
            start_x = (SIRKA - celkova_sirka) // 2
            for idx, znak in enumerate(skore_text):
                screen.blit(cisla[znak], (start_x + idx * 35, 25))

            screen.blit(font_maly.render("HRAC: " + jmeno_hrace.upper(), True, (255, 255, 255)), (15, 15))
            screen.blit(font_maly.render("CAS: " + str(cas_ms // 1000), True, (255, 255, 255)), (15, 40))

        if not hra_zacala and not game_over:
            klavesa_txt = pygame.key.name(fly_up_key).upper()
            info = font_velky.render("PRESS " + klavesa_txt + " TO FLY", True, (255, 230, 0))
            screen.blit(info, info.get_rect(center=(SIRKA // 2, 165)))

        # obrazovka po prohre (vlevo MEDAL + ikona, vpravo SCORE a CAS)
        if game_over:
            tmave = pygame.Surface((SIRKA, VYSKA), pygame.SRCALPHA)
            tmave.fill((0, 0, 0, 120))
            screen.blit(tmave, (0, 0))

            screen.blit(gameover_obr, gameover_obr.get_rect(center=(SIRKA // 2, 125)))

            panel_rect = gameover_panel_obr.get_rect(center=(SIRKA // 2, 305))
            screen.blit(gameover_panel_obr, panel_rect)

            # leva cast panelu - napis MEDAL vzdy, obrazek jen pokud hrac ziskal achievement
            medal_txt = font_maly.render("MEDAL", True, (255, 230, 90))
            screen.blit(medal_txt, medal_txt.get_rect(center=(panel_rect.left + 125, panel_rect.top + 45)))
            if len(ziskane_ach) > 0:
                nejvyssi_nazev, _ = ziskane_ach[-1]
                obr_ach = ach_obrazky[nejvyssi_nazev]
                screen.blit(obr_ach, obr_ach.get_rect(center=(panel_rect.left + 125, panel_rect.top + 138)))

            # prava cast panelu - SCORE a CAS pod sebou
            prav_x = panel_rect.right - 125
            lbl_score = font_maly.render("SCORE", True, (255, 230, 90))
            val_score = font_velky.render(str(skore), True, (255, 255, 255))
            lbl_cas = font_maly.render("CAS", True, (255, 230, 90))
            val_cas = font_velky.render(str(max(1, cas_ms // 1000)), True, (255, 255, 255))

            screen.blit(lbl_score, lbl_score.get_rect(center=(prav_x, panel_rect.top + 45)))
            screen.blit(val_score, val_score.get_rect(center=(prav_x, panel_rect.top + 86)))
            screen.blit(lbl_cas, lbl_cas.get_rect(center=(prav_x, panel_rect.top + 140)))
            screen.blit(val_cas, val_cas.get_rect(center=(prav_x, panel_rect.top + 181)))

            znovu = font_maly.render("SPACE / KLIK = ZNOVU   |   ESC = MENU", True, (255, 255, 255))
            screen.blit(znovu, znovu.get_rect(center=(SIRKA // 2, 470)))

        pygame.display.flip()
