"""
SmartCampus AI - Script d'exécution et d'évaluation des tests LLM (SA-32, SA-33, SA-34)
Permet à Tasnime (SA-34) et Roua (SA-36) de tester le modèle sélectionné
sur le dataset SA-32 (filtrage possible par langue : tunisien, arabizi, fr, code_switching).

Usage :
    python agents/evaluation/evaluer_llm.py --langue tunisien
    python agents/evaluation/evaluer_llm.py --langue arabizi
    python agents/evaluation/evaluer_llm.py --all
"""

import argparse
import json
import sys
from pathlib import Path

# Chemins de référence
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "SA-32_dataset_evaluation_llm.json"

# Import de la configuration LLM officielle
try:
    from agents.llm_config import (
        SELECTED_MODEL,
        SYSTEM_PROMPT,
        GENERATION_CONFIG,
    )
except ImportError:
    # Fallback si exécuté directement depuis le sous-dossier
    sys.path.append(str(BASE_DIR.parent.parent))
    from agents.llm_config import (
        SELECTED_MODEL,
        SYSTEM_PROMPT,
        GENERATION_CONFIG,
    )


def charger_dataset(langue_filtre=None):
    """Charge le jeu de données d'évaluation SA-32 avec filtrage optionnel par langue."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset introuvable : {DATASET_PATH}")

    with open(DATASET_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    questions = data.get("dataset", [])
    if langue_filtre and langue_filtre.lower() != "all":
        questions = [q for q in questions if q.get("langue", "").lower() == langue_filtre.lower()]

    return questions


def afficher_recapitulatif(questions, langue):
    """Affiche un résumé clair des tests prêts à être exécutés."""
    print("=" * 70)
    print("  SmartCampus AI — Module d'Évaluation LLM (Tâches SA-32 / SA-33 / SA-34)")
    print(f"  Modèle cible : {SELECTED_MODEL}")
    print(f"  Filtre langue : {langue if langue else 'Toutes (FR, Tunisien, Arabizi)'}")
    print(f"  Nombre de cas de test sélectionnés : {len(questions)}")
    print("=" * 70)

    for q in questions:
        print(f"\n[{q['id']}] ({q['langue'].upper()}) - Catégorie : {q['categorie']}")
        print(f"  Q : {q['question']}")
        print(f"  Intention attendue : {q['intention_attendue']}")
        print(f"  Éléments attendus : {', '.join(q['elements_reponse_attendus'][:2])}...")


def main():
    parser = argparse.ArgumentParser(description="Évaluateur de dialecte et LLM pour SmartCampus AI")
    parser.add_argument(
        "--langue",
        type=str,
        default="all",
        choices=["all", "fr", "tunisien", "arabizi", "code_switching"],
        help="Filtrer les tests par langue (ex: tunisien pour SA-34 de Tasnime)",
    )
    args = parser.parse_args()

    questions = charger_dataset(args.langue)
    afficher_recapitulatif(questions, args.langue)


if __name__ == "__main__":
    main()
