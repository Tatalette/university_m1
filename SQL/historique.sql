CREATE TABLE historique (
    id SERIAL PRIMARY KEY, -- Clé primaire auto-incrémentée
    nom_table VARCHAR(255), -- Nom de la table concernée
    type_maj CHAR(3), --type de mise à jour (INS, MOD, SUP)
    date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Date de la mise à jour
);