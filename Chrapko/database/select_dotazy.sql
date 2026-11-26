-- SELECT dotazy pro databazi flappy
USE flappy;

-- 1. vsechny hry s jmenem hrace a achievementy (JOIN, ORDER BY)
SELECT hra.id, user.jmeno, hra.score, hra.cas,
       GROUP_CONCAT(tag.nazev SEPARATOR ', ') AS achievementy
FROM hra
JOIN user ON hra.user_id = user.id
LEFT JOIN hra_tag ON hra.id = hra_tag.hra_id
LEFT JOIN tag ON hra_tag.tag_id = tag.id
GROUP BY hra.id, user.jmeno, hra.score, hra.cas
ORDER BY hra.score DESC;

-- 2. hry se skore aspon 50 (JOIN, WHERE, ORDER BY)
SELECT user.jmeno, hra.score, hra.cas
FROM hra
JOIN user ON hra.user_id = user.id
WHERE hra.score >= 50
ORDER BY hra.score DESC;

-- 3. hledani hrace podle jmena (JOIN, WHERE, LIKE)
SELECT user.jmeno, hra.score, hra.cas
FROM hra
JOIN user ON hra.user_id = user.id
WHERE user.jmeno LIKE '%a%'
ORDER BY hra.score DESC;

-- 4. statistiky hracu (JOIN, GROUP BY, ORDER BY)
SELECT user.jmeno, COUNT(hra.id) AS pocet_her, MAX(hra.score) AS max_score, ROUND(AVG(hra.score), 1) AS prumer
FROM user
JOIN hra ON user.id = hra.user_id
GROUP BY user.id, user.jmeno
ORDER BY max_score DESC;

-- 5. hraci a jejich nastavena klavesa (JOIN 1:1)
SELECT user.jmeno, nastaveni.key_binds
FROM user
JOIN nastaveni ON user.id = nastaveni.id;

-- 6. hry s konkretnim achievementem (JOIN M:N, WHERE)
SELECT user.jmeno, hra.score, tag.nazev
FROM hra
JOIN user ON hra.user_id = user.id
JOIN hra_tag ON hra.id = hra_tag.hra_id
JOIN tag ON hra_tag.tag_id = tag.id
WHERE tag.nazev = '20 trubek'
ORDER BY hra.score DESC;
