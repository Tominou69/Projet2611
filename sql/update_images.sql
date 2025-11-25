-- Associe chaque morpion à un fichier tX.png situé dans website/static/img/morpions/
-- Adapter si vous ajoutez/enlevez des morpions.

UPDATE morpion SET image = 'static/img/morpions/t1.png'  WHERE nom = 'Dragon Rouge';
UPDATE morpion SET image = 'static/img/morpions/t2.png'  WHERE nom = 'Gardien Ancien';
UPDATE morpion SET image = 'static/img/morpions/t3.png'  WHERE nom = 'Archimage';
UPDATE morpion SET image = 'static/img/morpions/t4.png'  WHERE nom = 'Ninja Précis';
UPDATE morpion SET image = 'static/img/morpions/t5.png'  WHERE nom = 'Berserker';
UPDATE morpion SET image = 'static/img/morpions/t6.png'  WHERE nom = 'Druide Serein';
UPDATE morpion SET image = 'static/img/morpions/t7.png'  WHERE nom = 'Chevalier Doré';
UPDATE morpion SET image = 'static/img/morpions/t8.png'  WHERE nom = 'Assassin Ombre';
UPDATE morpion SET image = 'static/img/morpions/t9.png'  WHERE nom = 'Spectre Azur';
UPDATE morpion SET image = 'static/img/morpions/t10.png' WHERE nom = 'Titan Runique';
UPDATE morpion SET image = 'static/img/morpions/t11.png' WHERE nom = 'Oracle Stellaire';
UPDATE morpion SET image = 'static/img/morpions/t12.png' WHERE nom = 'Guerrière Boréale';

-- Si vous avez d'autres morpions (jusqu'à t16.png), dupliquez les lignes ci-dessous
-- et remplacez le nom/tX.png appropriés.
-- UPDATE morpion SET image = 'static/img/morpions/t13.png' WHERE nom = '...';
-- UPDATE morpion SET image = 'static/img/morpions/t14.png' WHERE nom = '...';
-- UPDATE morpion SET image = 'static/img/morpions/t15.png' WHERE nom = '...';
-- UPDATE morpion SET image = 'static/img/morpions/t16.png' WHERE nom = '...';

