-- vzorova data do vsech tabulek
-- testovaci ucty:
-- kuba / heslo123
-- petr / ptacek42
-- anna / flappy99
-- martin / skore2026

USE flappy;

-- uzivatele
INSERT IGNORE INTO user (id, jmeno, heslo) VALUES
(1, 'kuba', 'nevim'),
(2, 'petr', 'nevim2'),
(3, 'anna', 'nevim3'),
(4, 'martin', 'nevim4');

-- nastaveni klaves
INSERT IGNORE INTO nastaveni (id, key_binds) VALUES
(1, 'up'),
(2, 'space'),
(3, 'w'),
(4, 'up');

-- achievementy (tagy) za 20, 50, 60 a 100 trubek
INSERT IGNORE INTO tag (id, nazev) VALUES
(1, '20 trubek'),
(2, '50 trubek'),
(3, '60 trubek'),
(4, '100 trubek');

-- odehrane hry
INSERT IGNORE INTO hra (id, user_id, score, cas) VALUES
(1, 1, 24, 52),
(2, 1, 63, 130),
(3, 2, 12, 28),
(4, 3, 52, 108),
(5, 3, 104, 215),
(6, 4, 21, 45);

-- prirazeni achievementu ke hram
INSERT IGNORE INTO hra_tag (hra_id, tag_id) VALUES
(1, 1),
(2, 1),
(2, 2),
(2, 3),
(4, 1),
(4, 2),
(5, 1),
(5, 2),
(5, 3),
(5, 4),
(6, 1);
