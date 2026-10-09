/* =============================================================================
   PROJET PFA - Service Social OCP 2026
   Creation des Dimensions + Fait -- types EXACTEMENT alignes sur staging_demandes
   (verifies via INFORMATION_SCHEMA.COLUMNS avant ecriture de ce script)
   ============================================================================= */

USE OCP_Social_2026;
GO


/* =============================================================================
   Dim_Agent (12 colonnes)
   ============================================================================= */
CREATE TABLE dbo.Dim_Agent (
    id_agent                        INT IDENTITY(1,1) PRIMARY KEY,
    matricule                       INT NOT NULL UNIQUE,
    nom_agent                       NVARCHAR(50) NOT NULL,
    prenom_agent                    NVARCHAR(50) NOT NULL,
    genre                           NVARCHAR(50) NOT NULL,
    situation_familiale             NVARCHAR(50) NOT NULL,
    categorie_professionnelle       NVARCHAR(60) NOT NULL,
    anciennete_annees               INT NOT NULL,
    categorie_anciennete            NVARCHAR(50) NOT NULL,
    annees_depuis_dernier_sejour    INT NOT NULL,
    nombre_points                   INT NOT NULL,
    site                            NVARCHAR(50) NOT NULL
);
GO

INSERT INTO dbo.Dim_Agent (matricule, nom_agent, prenom_agent, genre, situation_familiale,
    categorie_professionnelle, anciennete_annees, categorie_anciennete,
    annees_depuis_dernier_sejour, nombre_points, site)
SELECT DISTINCT
    matricule, nom_agent, prenom_agent, genre, situation_familiale,
    categorie_professionnelle, anciennete_annees, categorie_anciennete,
    annees_depuis_dernier_sejour, nombre_points, site
FROM dbo.staging_demandes;
GO

SELECT COUNT(*) AS nb_agents FROM dbo.Dim_Agent;   -- attendu : 4350


/* =============================================================================
   Dim_Etablissement (4 colonnes)
   ============================================================================= */
CREATE TABLE dbo.Dim_Etablissement (
    id_etablissement    INT IDENTITY(1,1) PRIMARY KEY,
    nom_etablissement    NVARCHAR(60) NOT NULL UNIQUE,
    ville                NVARCHAR(50) NOT NULL,
    type_produit         NVARCHAR(50) NOT NULL
);
GO

INSERT INTO dbo.Dim_Etablissement (nom_etablissement, ville, type_produit)
SELECT DISTINCT nom_etablissement, ville, type_produit
FROM dbo.staging_demandes;
GO

SELECT COUNT(*) AS nb_etablissements FROM dbo.Dim_Etablissement;


/* =============================================================================
   Dim_Periode (7 colonnes) -- type_produit indispensable dans le grain
   (Chalets et Residences/Hotels-Clubs = 2 calendriers differents qui
   partagent par coincidence les memes libelles P1 a P9)
   ============================================================================= */
CREATE TABLE dbo.Dim_Periode (
    id_periode_sk               INT IDENTITY(1,1) PRIMARY KEY,
    type_produit                 NVARCHAR(50) NOT NULL,
    id_periode                   NVARCHAR(50) NOT NULL,
    saison                       NVARCHAR(50) NOT NULL,
    periode_classement_debut     DATE NOT NULL,
    periode_classement_fin       DATE NOT NULL,
    date_limite_demande          DATE NOT NULL,
    date_limite_paiement         DATE NOT NULL
);
GO

INSERT INTO dbo.Dim_Periode (type_produit, id_periode, saison,
    periode_classement_debut, periode_classement_fin, date_limite_demande, date_limite_paiement)
SELECT DISTINCT
    type_produit, id_periode, saison,
    periode_classement_debut, periode_classement_fin,
    date_limite_demande, date_limite_paiement
FROM dbo.staging_demandes;
GO

SELECT COUNT(*) AS nb_periodes FROM dbo.Dim_Periode;   -- attendu : 54

-- Verification de securite : aucune ambiguite ne doit subsister
SELECT type_produit, saison, id_periode, COUNT(*) AS nb
FROM dbo.Dim_Periode
GROUP BY type_produit, saison, id_periode
HAVING COUNT(*) > 1;   -- doit renvoyer 0 ligne


/* =============================================================================
   Dim_Temps (11 colonnes) -- generee, pas issue des donnees
   ============================================================================= */
CREATE TABLE dbo.Dim_Temps (
    id_date              DATE PRIMARY KEY,
    date_complete        DATE NOT NULL,
    jour                 INT,
    mois                 INT,
    nom_mois             NVARCHAR(20),
    trimestre            INT,
    annee                INT,
    semaine              INT,
    jour_semaine         INT,
    nom_jour             NVARCHAR(20),
    week_end             BIT
);
GO

DECLARE @date_debut DATE = '2025-12-01';
DECLARE @date_fin   DATE = '2026-09-30';

;WITH Calendrier AS (
    SELECT @date_debut AS date_du_jour
    UNION ALL
    SELECT DATEADD(DAY, 1, date_du_jour)
    FROM Calendrier
    WHERE date_du_jour < @date_fin
)
INSERT INTO dbo.Dim_Temps
SELECT
    date_du_jour,
    date_du_jour,
    DAY(date_du_jour),
    MONTH(date_du_jour),
    DATENAME(MONTH, date_du_jour),
    DATEPART(QUARTER, date_du_jour),
    YEAR(date_du_jour),
    DATEPART(WEEK, date_du_jour),
    DATEPART(WEEKDAY, date_du_jour),
    DATENAME(WEEKDAY, date_du_jour),
    CASE WHEN DATEPART(WEEKDAY, date_du_jour) IN (1,7) THEN 1 ELSE 0 END
FROM Calendrier
OPTION (MAXRECURSION 366);
GO

SELECT COUNT(*) AS nb_jours FROM dbo.Dim_Temps;


/* =============================================================================
   Fait_Demandes (34 colonnes) -- types alignes sur staging (DECIMAL(10,4)
   pour montants et taux, comme dans ta table staging_demandes)
   Sans type_vue_config ni capacite_logement (doublons retires)
   ============================================================================= */
CREATE TABLE dbo.Fait_Demandes (
    numero_demande                     NVARCHAR(50) PRIMARY KEY,

    id_agent                           INT NOT NULL,
    id_etablissement                   INT NOT NULL,
    id_periode_sk                      INT NOT NULL,
    id_date_demande                    DATE NOT NULL,
    id_date_debut_sejour               DATE NOT NULL,
    id_date_fin_sejour                 DATE NOT NULL,
    id_date_traitement                 DATE NOT NULL,
    id_date_paiement                   DATE NULL,
    id_date_tirage_voucher             DATE NULL,

    nombre_nuitees                     INT NOT NULL,
    nombre_enfants                     INT NOT NULL,
    nombre_accompagnants                INT NOT NULL,
    nombre_enfants_chambre_parents      INT NOT NULL,
    total_membres_famille              INT NOT NULL,
    nombre_chambres_double             INT NOT NULL,
    nombre_chambres_simple             INT NOT NULL,
    nombre_pieces                      INT NOT NULL,
    montant_total_sejour               DECIMAL(10,4) NOT NULL,
    quote_part_agent                   DECIMAL(10,4) NOT NULL,
    montant_pris_charge_ocp            DECIMAL(10,4) NOT NULL,
    taux_prise_charge_ocp              DECIMAL(10,4) NOT NULL,
    taux_participation_agent           DECIMAL(10,4) NOT NULL,
    cout_par_personne                  DECIMAL(10,4) NOT NULL,
    rang_classement                    INT NOT NULL,
    delai_traitement_jours             INT NOT NULL,
    delai_paiement_jours               INT NULL,
    anticipation_reservation_jours     INT NOT NULL,

    type_vue                           NVARCHAR(50) NOT NULL,
    formule_restauration               NVARCHAR(50) NOT NULL,
    statut_apres_classement            NVARCHAR(50) NOT NULL,
    reference_paiement                 INT NULL,
    statut_paiement                    NVARCHAR(50) NOT NULL,
    numero_voucher                     NVARCHAR(50) NULL,
    statut_demande                     NVARCHAR(50) NOT NULL,
    categorie_taille_groupe            NVARCHAR(50) NOT NULL,

    CONSTRAINT FK_Fait_Agent           FOREIGN KEY (id_agent)          REFERENCES dbo.Dim_Agent(id_agent),
    CONSTRAINT FK_Fait_Etablissement   FOREIGN KEY (id_etablissement)  REFERENCES dbo.Dim_Etablissement(id_etablissement),
    CONSTRAINT FK_Fait_Periode         FOREIGN KEY (id_periode_sk)     REFERENCES dbo.Dim_Periode(id_periode_sk),
    CONSTRAINT FK_Fait_DateDemande     FOREIGN KEY (id_date_demande)   REFERENCES dbo.Dim_Temps(id_date),
    CONSTRAINT FK_Fait_DateDebut       FOREIGN KEY (id_date_debut_sejour) REFERENCES dbo.Dim_Temps(id_date),
    CONSTRAINT FK_Fait_DateFin         FOREIGN KEY (id_date_fin_sejour) REFERENCES dbo.Dim_Temps(id_date),
    CONSTRAINT FK_Fait_DateTraitement  FOREIGN KEY (id_date_traitement) REFERENCES dbo.Dim_Temps(id_date),
    CONSTRAINT FK_Fait_DatePaiement    FOREIGN KEY (id_date_paiement)  REFERENCES dbo.Dim_Temps(id_date),
    CONSTRAINT FK_Fait_DateVoucher     FOREIGN KEY (id_date_tirage_voucher) REFERENCES dbo.Dim_Temps(id_date)
);
GO

INSERT INTO dbo.Fait_Demandes (
    numero_demande, id_agent, id_etablissement, id_periode_sk,
    id_date_demande, id_date_debut_sejour, id_date_fin_sejour, id_date_traitement,
    id_date_paiement, id_date_tirage_voucher,
    nombre_nuitees, nombre_enfants, nombre_accompagnants, nombre_enfants_chambre_parents,
    total_membres_famille, nombre_chambres_double, nombre_chambres_simple, nombre_pieces,
    montant_total_sejour, quote_part_agent, montant_pris_charge_ocp,
    taux_prise_charge_ocp, taux_participation_agent, cout_par_personne,
    rang_classement, delai_traitement_jours, delai_paiement_jours, anticipation_reservation_jours,
    type_vue, formule_restauration, statut_apres_classement, reference_paiement,
    statut_paiement, numero_voucher, statut_demande, categorie_taille_groupe
)
SELECT
    s.numero_demande,
    da.id_agent,
    de.id_etablissement,
    dp.id_periode_sk,
    s.date_demande,
    s.date_debut_sejour,
    s.date_fin_sejour,
    s.date_traitement,
    s.date_paiement,
    s.date_tirage_voucher,
    s.nombre_nuitees, s.nombre_enfants, s.nombre_accompagnants, s.nombre_enfants_chambre_parents,
    s.total_membres_famille, s.nombre_chambres_double, s.nombre_chambres_simple, s.nombre_pieces,
    s.montant_total_sejour, s.quote_part_agent, s.montant_pris_charge_ocp,
    s.taux_prise_charge_ocp, s.taux_participation_agent, s.cout_par_personne,
    s.rang_classement, s.delai_traitement_jours, s.delai_paiement_jours, s.anticipation_reservation_jours,
    s.type_vue, s.formule_restauration, s.statut_apres_classement, s.reference_paiement,
    s.statut_paiement, s.numero_voucher, s.statut_demande, s.categorie_taille_groupe
FROM dbo.staging_demandes s
JOIN dbo.Dim_Agent da         ON da.matricule = s.matricule
JOIN dbo.Dim_Etablissement de ON de.nom_etablissement = s.nom_etablissement
JOIN dbo.Dim_Periode dp       ON dp.type_produit = s.type_produit
                              AND dp.saison = s.saison
                              AND dp.id_periode = s.id_periode;
GO


/* =============================================================================
   Verifications finales
   ============================================================================= */
SELECT
    (SELECT COUNT(*) FROM dbo.staging_demandes) AS nb_staging,
    (SELECT COUNT(*) FROM dbo.Fait_Demandes)    AS nb_faits;   -- doivent etre egaux (5000)

SELECT 'Agent orphelin' AS test, COUNT(*) AS n
FROM dbo.Fait_Demandes f WHERE NOT EXISTS (SELECT 1 FROM dbo.Dim_Agent WHERE id_agent = f.id_agent)
UNION ALL
SELECT 'Etablissement orphelin', COUNT(*)
FROM dbo.Fait_Demandes f WHERE NOT EXISTS (SELECT 1 FROM dbo.Dim_Etablissement WHERE id_etablissement = f.id_etablissement)
UNION ALL
SELECT 'Periode orpheline', COUNT(*)
FROM dbo.Fait_Demandes f WHERE NOT EXISTS (SELECT 1 FROM dbo.Dim_Periode WHERE id_periode_sk = f.id_periode_sk);
-- les 3 doivent afficher 0

-- Index de performance
CREATE INDEX IX_Fait_Agent ON dbo.Fait_Demandes(id_agent);
CREATE INDEX IX_Fait_Etablissement ON dbo.Fait_Demandes(id_etablissement);
CREATE INDEX IX_Fait_Periode ON dbo.Fait_Demandes(id_periode_sk);
GO