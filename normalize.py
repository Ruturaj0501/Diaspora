import json
import re
import os
import jellyfish
import dateparser
from rapidfuzz import process, fuzz
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
load_dotenv() 

print("[INFO] Loading LangChain Hugging Face embeddings...")


if not os.getenv('HF_TOKEN'):
    print("[WARNING] HF_TOKEN environment variable not found. Some models may require it.")

os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', '')
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


NAME_VARIANTS = {
    "jno": "John",
    "wm": "William",
    "chas": "Charles",
    "geo": "George",
    "thos": "Thomas",
    "jas": "James",
    "rob't": "Robert",
    "robt": "Robert",
    "saml": "Samuel"
}


PLACE_GAZETTEER = {
    "Charleston, South Carolina": ["Charleston", "Chas. Dist.", "Charleston Dist.", "Chas, SC"],
    "New Orleans, Louisiana": ["N.O.", "New Orleans", "Orleans Parish"],
    "Savannah, Georgia": ["Savannah", "Savh", "Chatham County"]
}
FLAT_ALIASES = {alias.lower(): standard_name for standard_name, aliases in PLACE_GAZETTEER.items() for alias in aliases}


def normalize_name(name_str):
    """
    Goal 1: Name Normalization API (Variant + Phonetic + LangChain Embedding)
    """
    clean_name = name_str.lower().strip()
    
    
    words = clean_name.split()
    standardized_words = [NAME_VARIANTS.get(w, w) for w in words]
    standardized_name = " ".join(standardized_words)
    
    
    phonetic_key = jellyfish.metaphone(standardized_name)
    
    
    embedding_vector = embeddings.embed_query(standardized_name)
    
    return {
        "standardized_name": standardized_name.title(),
        "phonetic_key": phonetic_key,
        "embedding": embedding_vector 
    }

def normalize_place(place_str):
    """
    Goal 2: Place Resolution API (Fuzzy Matching)
    """
    clean_place = place_str.lower().strip()
    match = process.extractOne(clean_place, FLAT_ALIASES.keys(), scorer=fuzz.WRatio, score_cutoff=80)
    
    if match:
        matched_alias = match[0]
        return FLAT_ALIASES[matched_alias]
    
    return f"UNRESOLVED: {place_str}"

def normalize_date(date_str):
    """
    Goal 3: Date Normalization API (Fuzzy Dates -> Ranges)
    """
    clean_date_str = re.sub(r'(?i)\bday of\b', '', date_str)
    parsed_date = dateparser.parse(clean_date_str)
    
    if parsed_date:
        iso_date = parsed_date.strftime("%Y-%m-%d")
        return {
            "date_start": iso_date,
            "date_end": iso_date
        }
    
    return f"UNRESOLVED: {date_str}"


def main():
    print("[INFO] Loading Phase 2 extracted data...")
    try:
        with open("phase2_output.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[ERROR] phase2_output.json not found. Run Phase 2 first.")
        return

    print("[INFO] Normalizing extracted entities...")
    normalized_entities = []
    
    for ent in data.get("entities", []):
        raw_text = ent["entity"]
        label = ent["label"]
        processed_ent = ent.copy()
        
        if label == "PERSON":
            processed_ent["normalized_data"] = normalize_name(raw_text)
            print(f"Normalized [PERSON] '{raw_text}' -> '{processed_ent['normalized_data']['standardized_name']}' ({processed_ent['normalized_data']['phonetic_key']})")
        
        elif label == "PLACE":
            processed_ent["normalized_data"] = normalize_place(raw_text)
            print(f"Normalized [PLACE] '{raw_text}' -> '{processed_ent['normalized_data']}'")
        
        elif label == "DATE":
            processed_ent["normalized_data"] = normalize_date(raw_text)
            print(f"Normalized [DATE] '{raw_text}' -> '{processed_ent['normalized_data']}'")
        
        else:
            processed_ent["normalized_data"] = raw_text
            print(f"Passed through [{label}] '{raw_text}'")

        normalized_entities.append(processed_ent)

    data["entities"] = normalized_entities

    with open("phase3_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("\n[SUCCESS] Phase 3 completed.")
    print("[SUCCESS] Output saved to phase3_output.json")

if __name__ == "__main__":
    main()