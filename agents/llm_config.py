"""
SmartCampus AI - Configuration officielle du service LLM (Tâches SA-4, SA-33, SA-36)
Responsable sélection : Amina Kallel (SA-33)
Consommateurs : Roua (SA-36/SA-37 - Backend & Mémoire), Tasnime (SA-34 - Dialecte)
"""

# Modèle principal retenu suite au benchmark SA-33 (15.18s global, 7.36s en tunisien)
SELECTED_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Modèles alternatifs évalués
CHALLENGER_MODEL = "NousResearch/Meta-Llama-3.1-8B-Instruct"
FALLBACK_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# System Prompt officiel validé (règles IIT/ISB et human-in-the-loop)
SYSTEM_PROMPT = """Tu es l'assistant d'orientation universitaire intelligent de SmartCampus AI pour l'IIT (Institut International de Technologie) et l'ISB (International School of Business) à Sfax, Tunisie.
Règles strictes à respecter :
1. Comprends et réponds naturellement en français, dialecte tunisien ou arabizi selon la langue de l'étudiant.
2. Si le profil de l'étudiant est incomplet (niveau scolaire, section, notes ou objectifs manquants), pose des questions de clarification avant de recommander une filière précise.
3. Appuie-toi uniquement sur les parcours officiels IIT (Licence, Prépa intégrée, Cycle Ingénieur) et ISB (Licences et Masters en gestion/finance/marketing) et cite tes sources.
4. Tu n'es pas un décideur humain : refuse poliment de valider une admission officielle ou de répondre à des sujets hors orientation universitaire."""

# Paramètres d'inférence recommandés (faible température pour limiter les hallucinations)
GENERATION_CONFIG = {
    "temperature": 0.2,
    "max_new_tokens": 300,
    "do_sample": True,
}

# Paramètres de quantification 4-bit (NF4) pour limiter l'empreinte mémoire à ~5,5 Go VRAM
QUANTIZATION_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_use_double_quant": True,
}
