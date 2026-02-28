import json
import re
import os
import jellyfish
import dateparser
from rapidfuzz import process, fuzz
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

print("[INFO] Loading HuggingFace embeddings...")

if not os.getenv("HF_TOKEN"):
    print("[WARNING] HF_TOKEN not found. Using public access.")

os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN", "")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# -----------------------------
# DATA
# -----------------------------

MONTHS = {
    "january","february","march","april","may","june",
    "july","august","september","october","november","december"
}

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

# Load alias corpus
with open("phase_3/alias_corpus.json", "r", encoding="utf-8") as f:
    ALIAS_DATA = json.load(f)

PLACE_GAZETTEER = ALIAS_DATA["places"]

FLAT_ALIASES = {
    alias.lower(): standard
    for standard, aliases in PLACE_GAZETTEER.items()
    for alias in aliases
}

# -----------------------------
# NAME NORMALIZATION
# -----------------------------

def normalize_name(name):

    clean = name.lower().strip()

    words = clean.split()
    fixed_words = [NAME_VARIANTS.get(w, w) for w in words]
    standard = " ".join(fixed_words)

    phonetic = jellyfish.metaphone(standard)

    embedding = embeddings.embed_query(standard)

    return {
        "standardized_name": standard.title(),
        "phonetic_key": phonetic,
        "embedding": embedding
    }

# -----------------------------
# PLACE NORMALIZATION
# -----------------------------

def normalize_place(place):

    clean = place.lower().strip()

    match = process.extractOne(
        clean,
        list(FLAT_ALIASES.keys()),
        scorer=fuzz.WRatio
    )

    if match and match[1] >= 80:
        return FLAT_ALIASES[match[0]]

    return f"UNRESOLVED: {place}"

# -----------------------------
# DATE NORMALIZATION
# -----------------------------

def normalize_date(date_text):

    clean = re.sub(r'(?i)\bday of\b', '', date_text)

    parsed = dateparser.parse(
        clean,
        settings={
            "PREFER_DAY_OF_MONTH": "first",
            "PREFER_DATES_FROM": "past"
        }
    )

    if parsed:
        iso = parsed.strftime("%Y-%m-%d")
        return {
            "date_start": iso,
            "date_end": iso
        }

    return f"UNRESOLVED: {date_text}"


# -----------------------------
# STABLE KEY GENERATOR
# -----------------------------

def make_key(name):
    return name.lower().replace(",", "").replace(" ", "_")
# -----------------------------
# LABEL CORRECTION
# -----------------------------

def correct_label(text, label):

    t = text.lower().strip()

    if label == "PERSON" and t in MONTHS:
        return "DATE"

    if label == "PERSON" and t in FLAT_ALIASES:
        return "PLACE"

    return label

# -----------------------------
# MAIN
# -----------------------------

def main():

    print("[INFO] Loading Phase 2 output...")

    try:
        with open("phase2_output.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[ERROR] phase2_output.json not found.")
        return

    print("[INFO] Normalizing entities...")

    normalized = []

    for ent in data.get("entities", []):

        raw = ent.get("text", "")
        label = ent.get("label", "")

        label = correct_label(raw, label)

        obj = ent.copy()

        if label == "PERSON":

            result = normalize_name(raw)
            obj["normalized_data"] = result

            print(f"Normalized [PERSON] '{raw}' -> '{result['standardized_name']}'")

        elif label == "PLACE":

            result = normalize_place(raw)
            obj["normalized_data"] = result
            obj["normalized_key"] = make_key(result)

            print(f"Normalized [PLACE] {raw} -> {result}")

        elif label == "DATE":

            result = normalize_date(raw)
            obj["normalized_data"] = result

            print(f"Normalized [DATE] {raw} -> {result}")

        else:

            obj["normalized_data"] = raw
            print(f"Passed [{label}] {raw}")

        obj["confidence"] = ent.get("score", 0.9)

        normalized.append(obj)

    data["entities"] = normalized

    with open("phase3_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("\n[SUCCESS] Phase 3 completed.")
    print("[SUCCESS] Output saved to phase3_output.json")

# -----------------------------

if __name__ == "__main__":
    main()