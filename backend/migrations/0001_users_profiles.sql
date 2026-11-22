-- SA-17: comptes, profils candidats et relations associées.
-- PostgreSQL 12+. À appliquer une seule fois, après sauvegarde de la base cible.
-- Cette migration crée uniquement le schéma; elle ne charge aucune donnée.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;

DO $$
BEGIN
    IF to_regtype('public.role_utilisateur') IS NULL THEN
        CREATE TYPE public.role_utilisateur AS ENUM ('candidat', 'admin');
    END IF;
    IF to_regtype('public.langue_echange') IS NULL THEN
        CREATE TYPE public.langue_echange AS ENUM ('fr', 'tunisien', 'arabizi');
    END IF;
    IF to_regtype('public.etablissement_cible') IS NULL THEN
        CREATE TYPE public.etablissement_cible AS ENUM ('IIT', 'ISB', 'indifferent');
    END IF;
    IF to_regtype('public.mode_contact') IS NULL THEN
        CREATE TYPE public.mode_contact AS ENUM ('email', 'telephone');
    END IF;
END
$$;

CREATE TABLE public.utilisateur (
    id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role public.role_utilisateur NOT NULL DEFAULT 'candidat',
    langue_preferee public.langue_echange NOT NULL DEFAULT 'fr',
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    derniere_connexion TIMESTAMPTZ,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_utilisateur_email_format
        CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);

CREATE UNIQUE INDEX ux_utilisateur_email_lower
    ON public.utilisateur (lower(email));

CREATE TABLE public.profil_candidat (
    id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),
    utilisateur_id UUID NOT NULL UNIQUE
        REFERENCES public.utilisateur(id) ON DELETE CASCADE,
    telephone VARCHAR(20)
        CHECK (telephone IS NULL OR telephone ~ '^\+?[0-9]{8,15}$'),
    date_naissance DATE
        CHECK (date_naissance IS NULL OR date_naissance <= CURRENT_DATE),
    ville VARCHAR(100),
    gouvernorat VARCHAR(50),
    pays VARCHAR(60) NOT NULL DEFAULT 'Tunisie',
    adresse TEXT,
    niveau_etudes VARCHAR(100),
    serie_bac VARCHAR(60),
    etablissement_origine VARCHAR(150),
    annee_obtention SMALLINT
        CHECK (annee_obtention IS NULL OR annee_obtention BETWEEN 1990 AND 2100),
    moyenne_generale NUMERIC(4,2)
        CHECK (moyenne_generale IS NULL OR moyenne_generale BETWEEN 0 AND 20),
    objectifs TEXT,
    etablissement_prefere public.etablissement_cible
        NOT NULL DEFAULT 'indifferent',
    mode_contact_prefere public.mode_contact NOT NULL DEFAULT 'email',
    cree_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.resultat_scolaire (
    id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),
    profil_id UUID NOT NULL
        REFERENCES public.profil_candidat(id) ON DELETE CASCADE,
    matiere VARCHAR(100) NOT NULL,
    periode VARCHAR(50) NOT NULL,
    note NUMERIC(4,2) NOT NULL CHECK (note BETWEEN 0 AND 20),
    coefficient NUMERIC(4,2) NOT NULL DEFAULT 1 CHECK (coefficient > 0),
    CONSTRAINT uq_resultat_profil_matiere_periode
        UNIQUE (profil_id, matiere, periode)
);

CREATE TABLE public.interet (
    id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),
    libelle VARCHAR(100) NOT NULL UNIQUE,
    categorie VARCHAR(60)
);

CREATE TABLE public.profil_interet (
    profil_id UUID NOT NULL
        REFERENCES public.profil_candidat(id) ON DELETE CASCADE,
    interet_id UUID NOT NULL
        REFERENCES public.interet(id) ON DELETE RESTRICT,
    ajoute_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (profil_id, interet_id)
);

CREATE TABLE public.session_visiteur (
    session_id UUID PRIMARY KEY DEFAULT public.gen_random_uuid(),
    utilisateur_id UUID
        REFERENCES public.utilisateur(id) ON DELETE SET NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    expire_le TIMESTAMPTZ NOT NULL,
    rattachee_le TIMESTAMPTZ,
    CONSTRAINT ck_session_visiteur_expiration CHECK (expire_le > cree_le)
);

CREATE INDEX ix_resultat_scolaire_profil
    ON public.resultat_scolaire (profil_id);
CREATE INDEX ix_profil_interet_interet
    ON public.profil_interet (interet_id);
CREATE INDEX ix_session_visiteur_utilisateur
    ON public.session_visiteur (utilisateur_id);
CREATE INDEX ix_session_visiteur_expiration
    ON public.session_visiteur (expire_le);

CREATE OR REPLACE FUNCTION public.verifier_role_profil_candidat()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    role_compte public.role_utilisateur;
BEGIN
    SELECT u.role
      INTO role_compte
      FROM public.utilisateur AS u
     WHERE u.id = NEW.utilisateur_id
     FOR UPDATE;

    IF role_compte IS DISTINCT FROM 'candidat'::public.role_utilisateur THEN
        RAISE EXCEPTION 'Un profil candidat doit appartenir à un utilisateur candidat'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$function$;

CREATE TRIGGER trg_verifier_role_profil_candidat
    BEFORE INSERT OR UPDATE OF utilisateur_id
    ON public.profil_candidat
    FOR EACH ROW
    EXECUTE FUNCTION public.verifier_role_profil_candidat();

CREATE OR REPLACE FUNCTION public.empecher_admin_avec_profil()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.role <> 'candidat'::public.role_utilisateur
       AND EXISTS (
           SELECT 1
             FROM public.profil_candidat AS p
            WHERE p.utilisateur_id = NEW.id
       ) THEN
        RAISE EXCEPTION 'Un compte ayant un profil candidat ne peut pas devenir administrateur'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$function$;

CREATE TRIGGER trg_empecher_admin_avec_profil
    BEFORE UPDATE OF role
    ON public.utilisateur
    FOR EACH ROW
    WHEN (OLD.role IS DISTINCT FROM NEW.role)
    EXECUTE FUNCTION public.empecher_admin_avec_profil();

CREATE OR REPLACE FUNCTION public.mettre_a_jour_modifie_le()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.modifie_le = now();
    RETURN NEW;
END;
$function$;

CREATE TRIGGER trg_utilisateur_modifie_le
    BEFORE UPDATE ON public.utilisateur
    FOR EACH ROW
    EXECUTE FUNCTION public.mettre_a_jour_modifie_le();

CREATE TRIGGER trg_profil_candidat_modifie_le
    BEFORE UPDATE ON public.profil_candidat
    FOR EACH ROW
    EXECUTE FUNCTION public.mettre_a_jour_modifie_le();

CREATE OR REPLACE VIEW public.v_profil_completude AS
SELECT
    p.id AS profil_id,
    (p.niveau_etudes IS NOT NULL AND length(trim(p.niveau_etudes)) > 0) AS niveau_ok,
    EXISTS (
        SELECT 1 FROM public.resultat_scolaire AS r WHERE r.profil_id = p.id
    ) AS resultats_ok,
    EXISTS (
        SELECT 1 FROM public.profil_interet AS pi WHERE pi.profil_id = p.id
    ) AS interets_ok,
    (p.objectifs IS NOT NULL AND length(trim(p.objectifs)) > 0) AS objectifs_ok,
    (
        p.niveau_etudes IS NOT NULL
        AND length(trim(p.niveau_etudes)) > 0
        AND EXISTS (
            SELECT 1 FROM public.resultat_scolaire AS r WHERE r.profil_id = p.id
        )
        AND EXISTS (
            SELECT 1 FROM public.profil_interet AS pi WHERE pi.profil_id = p.id
        )
        AND p.objectifs IS NOT NULL
        AND length(trim(p.objectifs)) > 0
    ) AS est_complet
FROM public.profil_candidat AS p;

COMMIT;
