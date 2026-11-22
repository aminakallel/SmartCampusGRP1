import type { Etablissement, NiveauFormation, Programme } from "@/types";

/**
 * Catalogue de départ (IIT et ISB), d'après les pages officielles iit.tn et isb.tn.
 *
 * Les durées, conditions d'accès et débouchés ne figurent pas dans ces listes :
 * ils sont à compléter depuis l'espace équipe (Formations) avec les pages officielles.
 */

const slugify = (value: string) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

function programme(
  etablissement: Etablissement,
  niveau: NiveauFormation,
  nom: string,
  description: string,
  motsCles: string[],
  lien?: string,
): Programme {
  const id = slugify(`${etablissement} ${nom}`);
  return {
    id,
    slug: id,
    nom,
    etablissement,
    niveau,
    duree: "À renseigner",
    description,
    prerequis: [],
    debouches: [],
    motsCles,
    lien,
  };
}

export const MOCK_PROGRAMMES: Programme[] = [
  /* ---------------------------------- IIT ---------------------------------- */
  programme("IIT", "Préparatoire", "Cycle Préparatoire MP", "Cycle préparatoire MP de l’IIT.", ["préparatoire", "prépa", "MP", "mathématiques", "physique"]),

  programme("IIT", "Licence", "Licence en Systèmes Électriques Intelligents & Énergies Renouvelables", "Licence technologique en systèmes électriques intelligents et énergies renouvelables.", ["licence technologique", "électrique", "énergies renouvelables", "systèmes intelligents"], "https://iit.tn/licence-en-systemes-electriques-intelligents-energies-renouvelables/"),
  programme("IIT", "Licence", "Licence en Mécatronique & Systèmes Intelligents", "Licence technologique en mécatronique et systèmes intelligents.", ["licence technologique", "mécatronique", "systèmes intelligents"], "https://iit.tn/licence-en-mecatronique-systemes-intelligents/"),
  programme("IIT", "Licence", "Licence en Informatique : Réseaux et Cybersécurité", "Licence en informatique, parcours Réseaux et Cybersécurité.", ["informatique", "réseaux", "cybersécurité", "sécurité"], "https://iit.tn/reseaux-et-cybersecurite/"),
  programme("IIT", "Licence", "Licence en Informatique : Systèmes Embarqués & IoT", "Licence en informatique, parcours Systèmes Embarqués et Internet des Objets (IoT).", ["informatique", "systèmes embarqués", "IoT", "internet des objets"], "https://iit.tn/systemes-embarques-internet-des-objets-iot/"),
  programme("IIT", "Licence", "Licence en Informatique : Big Data et Analyse de Données", "Licence en informatique, parcours Big Data et Analyse de Données.", ["informatique", "big data", "analyse de données", "data"], "https://iit.tn/big-data-et-analyse-de-donnees/"),
  programme("IIT", "Licence", "Licence en Informatique : Génie Logiciel et Systèmes Intelligents", "Licence en informatique, parcours Génie Logiciel et Systèmes Intelligents.", ["informatique", "génie logiciel", "développement", "systèmes intelligents"], "https://iit.tn/genie-logiciel-systemes-intelligents/"),

  programme("IIT", "Ingénierie", "Cycle Ingénieur en Génie Civil", "Filière ingénieur en génie civil.", ["ingénieur", "génie civil"], "https://iit.tn/filieres-ingenieur/genie-civil/"),
  programme("IIT", "Ingénierie", "Cycle Ingénieur en Génie Mécanique", "Filière ingénieur en génie mécanique.", ["ingénieur", "génie mécanique", "mécanique"], "https://iit.tn/filieres-ingenieur/genie-mecanique-2/"),
  programme("IIT", "Ingénierie", "Cycle Ingénieur en Génie Informatique", "Filière ingénieur en génie informatique.", ["ingénieur", "génie informatique", "informatique"], "https://iit.tn/filieres-ingenieur/genie-informatique-2/"),
  programme("IIT", "Ingénierie", "Cycle Ingénieur en Génie Industriel", "Filière ingénieur en génie industriel.", ["ingénieur", "génie industriel", "industrie"], "https://iit.tn/filieres-ingenieur/genie-industriel-2/"),
  programme("IIT", "Ingénierie", "Cycle Ingénieur en Génie des Procédés", "Filière ingénieur en génie des procédés.", ["ingénieur", "génie des procédés", "procédés"], "https://iit.tn/genie-des-procedes/"),

  programme("IIT", "Architecture", "Architecture", "Formation en architecture de l’IIT.", ["architecture"]),
  programme("IIT", "Master", "Mastère Industries 4.0", "Mastère Industries 4.0 de l’IIT.", ["mastère", "master", "industrie 4.0", "industries 4.0"]),

  /* ---------------------------------- ISB ---------------------------------- */
  programme("ISB", "Licence", "Licence in Business Administration (ENG)", "Licence en administration des affaires couvrant la comptabilité, la finance, le marketing et d’autres disciplines. Formation enseignée en anglais.", ["administration des affaires", "business", "comptabilité", "finance", "marketing", "anglais"], "https://isb.tn/program-lba/"),
  programme("ISB", "Licence", "Licence in Business Intelligence (Bilingue)", "Licence en Business Intelligence, proposée en formation bilingue.", ["business intelligence", "bilingue"], "https://isb.tn/business-intelligence/"),
  programme("ISB", "Licence", "Licence nationale en Gestion : Management", "Licence nationale en gestion, avec une formation spécialisée dans le domaine du management. Enseignée en français.", ["gestion", "management", "français"], "https://isb.tn/management/"),
  programme("ISB", "Licence", "Licence nationale en Gestion : Comptabilité", "Licence nationale en comptabilité : formation d’étudiants spécialisés dans les domaines de la comptabilité. Enseignée en français.", ["gestion", "comptabilité", "français"], "https://isb.tn/comptabilite/"),
  programme("ISB", "Licence", "Licence nationale en Gestion : Finance", "Licence nationale en finance : formation de cadres spécialisés dans les domaines de la finance. Enseignée en français.", ["gestion", "finance", "français"], "https://isb.tn/finance/"),
  programme("ISB", "Licence", "Licence nationale en Gestion : Logistique et production", "Licence nationale en logistique et production : formation d’étudiants spécialisés dans la logistique et la production. Enseignée en français.", ["gestion", "logistique", "production", "français"], "https://isb.tn/logistique-et-production/"),
  programme("ISB", "Licence", "Licence nationale en Gestion : Marketing", "Licence en marketing, qui prépare l’étudiant à une carrière de cadre intermédiaire en marketing opérationnel. Enseignée en français.", ["gestion", "marketing", "français"], "https://isb.tn/marketing/"),
  programme("ISB", "Licence", "Licence nationale en Gestion : Ressources humaines", "Formation visant à doter les étudiants de connaissances théoriques et pratiques en gestion des ressources humaines. Enseignée en français.", ["gestion", "ressources humaines", "RH", "français"], "https://isb.tn/ressources-humaines/"),
  programme("ISB", "Licence", "Licence en Sciences Économiques : Business Economics (FR)", "Licence nationale en Business Economics, qui forme des économistes. Enseignée en français.", ["sciences économiques", "économie", "business economics", "français"], "https://isb.tn/business-economics-2/"),
  programme("ISB", "Licence", "Licence en Sciences Économiques : Transport et Logistique (FR)", "Licence en sciences économiques, parcours Transport et Logistique. Enseignée en français.", ["sciences économiques", "transport", "logistique", "français"]),
  programme("ISB", "Licence", "Licence nationale en Droit : Droit des affaires", "Licence nationale en droit des affaires : former des étudiants capables de maîtriser les principes du droit en général.", ["droit", "droit des affaires", "juridique"], "https://isb.tn/droit-des-affaires-2/"),
  programme("ISB", "Licence", "Licence nationale en Droit : Droit privé", "Licence nationale en droit, parcours Droit privé.", ["droit", "droit privé", "juridique"], "https://isb.tn/droit-prive-2/"),

  programme("ISB", "Master", "Mastère en Marketing Digital (FR)", "Mastère en marketing digital, enseigné en français.", ["mastère", "master", "marketing digital", "français"], "https://isb.tn/mmd/"),
  programme("ISB", "Master", "Master in Business Administration (MBA) (ENG)", "Master en administration des affaires (MBA), enseigné en anglais.", ["MBA", "master", "business administration", "anglais"], "https://isb.tn/program-mba/"),
  programme("ISB", "Master", "Mastère en Comptabilité (FR)", "Mastère en comptabilité, enseigné en français.", ["mastère", "master", "comptabilité", "français"], "https://isb.tn/program-mpc/"),
  programme("ISB", "Master", "Mastère Finance d’Entreprise et Ingénierie Financière (FR)", "Mastère en finance d’entreprise et ingénierie financière, enseigné en français.", ["mastère", "master", "finance d’entreprise", "ingénierie financière", "français"], "https://isb.tn/program-minf/"),
  programme("ISB", "Master", "Master of Science (MSc) in Digital Marketing (ENG)", "Master of Science en marketing digital, enseigné en anglais.", ["MSc", "master", "digital marketing", "marketing digital", "anglais"], "https://isb.tn/mmd-en/"),
  programme("ISB", "Master", "Master of Science (MSc) in Finance (ENG)", "Master of Science en finance, enseigné en anglais.", ["MSc", "master", "finance", "anglais"], "https://isb.tn/program-msf/"),
  programme("ISB", "Master", "Master in Business Law (ENG)", "Master en droit des affaires, enseigné en anglais.", ["master", "business law", "droit des affaires", "anglais"]),
];