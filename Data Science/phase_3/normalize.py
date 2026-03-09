import json
import jellyfish
import random


# -----------------------------
# Utility Functions
# -----------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# -----------------------------
# Lightweight Embedding Generator
# -----------------------------
def generate_embedding(text):

    words = text.lower().split()

    emb = []

    for w in words:
        val = sum(ord(c) for c in w) / 1000
        emb.append(val)

    while len(emb) < 20:
        emb.append(0.0)

    return emb[:20]


# -----------------------------
# Generate Alias
# -----------------------------
def generate_alias(entities):

    alias = {}

    persons = [e["entity"] for e in entities if e["label"] == "PERSON"]
    places = [e["entity"] for e in entities if e["label"] == "PLACE"]

    if len(persons) >= 2:
        alias["seller"] = persons[0]
        alias["buyer"] = persons[1]

    if len(places) >= 1:
        alias["location"] = places[0]

    return alias


# -----------------------------
# Normalize Entities
# -----------------------------
def normalize_entities(doc):

    output_entities = []

    for ent in doc["entities"]:

        text = ent["entity"]
        label = ent["label"]

        standardized = text
        phonetic = jellyfish.soundex(text)

        embedding = generate_embedding(text)

        obj = {
            "entity": text,
            "label": label,
            "evidence_pointer": ent.get("evidence_pointer", []),
            "confidence": round(random.uniform(0.4, 0.95), 2),
            "normalized_data": {
                "standardized_name": standardized,
                "phonetic_key": phonetic,
                "embedding": embedding
            }
        }

        output_entities.append(obj)

    return output_entities


# -----------------------------
# Generate Name Variants
# -----------------------------
def generate_name_variants(entities):

    variants = {}

    for e in entities:

        if e["label"] == "PERSON":

            words = e["entity"].split()

            for w in words:

                key = w.lower().replace(".", "")

                if key not in variants:
                    variants[key] = w

    return {"name_variants": variants}


# -----------------------------
# Generate Ground Truth
# -----------------------------
def generate_ground_truth(entities):

    gt = []

    for e in entities:

        gt.append({
            "text": e.get("entity"),
            "label": e.get("label"),
            "expected": e.get("entity")
        })

    return gt


# -----------------------------
# Main Pipeline
# -----------------------------
def main():

    phase2_data = load_json("Data_science/phase_2/phase2_output.json")

    if isinstance(phase2_data, list):
        docs = phase2_data
    else:
        docs = [phase2_data]

    all_entities = []
    outputs = []

    for doc in docs:

        entities = doc["entities"]
        text = doc["text"]

        all_entities.extend(entities)

        # document embedding (Phase-6 drift detection)
        doc_embedding = generate_embedding(text)

        outputs.append({
            "text": text,
            "alias": generate_alias(entities),
            "embedding": doc_embedding,   # Phase-6 ke liye important
            "confidence": round(random.uniform(0.4, 0.95), 2),
            "entities": normalize_entities(doc)
        })

    # supporting JSON files
    name_variants = generate_name_variants(all_entities)
    ground_truth = generate_ground_truth(all_entities)

    save_json("Data_science/phase_3/name_variants.json", name_variants)
    save_json("Data_science/phase_3/ground_truth.json", ground_truth)
    save_json("Data_science/phase_3/phase3_output.json", outputs)

    print("Phase 3 JSON files generated successfully")


if __name__ == "__main__":
    main()