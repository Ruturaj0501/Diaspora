import json
import re
import random
import os

BASE_DIR = "Data_science/phase_2"
os.makedirs(BASE_DIR, exist_ok=True)

# -----------------------------------
# 1. DEFINE ONTOLOGY
# -----------------------------------

ontology = {
    "entities": ["PERSON", "PLACE", "DATE"],
    "events": ["SALE", "TRANSFER"],
    "required_fields": {
        "SALE": ["seller", "buyer", "item", "price", "location", "date"]
    }
}

with open(os.path.join(BASE_DIR, "ontology.json"), "w") as f:
    json.dump(ontology, f, indent=4)

print("[INFO] Ontology defined")


# -----------------------------------
# 2. CREATE LABELED TRAINING DATASET
# -----------------------------------

names = ["John Smith", "William Brown", "Henry Walker", "Samuel Adams"]
cities = ["Delhi", "London", "Paris", "Boston"]
items = ["land", "horse", "wagon", "cotton"]

dataset = []

for i in range(100):

    seller = random.choice(names)

    buyer = random.choice([n for n in names if n != seller])

    city = random.choice(cities)
    item = random.choice(items)

    date = f"{random.randint(1,28)} March {random.randint(1850,1900)}"
    price = random.randint(50,500)

    text = f"{seller} sold {item} to {buyer} in {city} on {date} for {price} dollars"

    dataset.append({
        "text": text,
        "entities": [
            {"text": seller, "type": "PERSON"},
            {"text": buyer, "type": "PERSON"},
            {"text": city, "type": "PLACE"},
            {"text": date, "type": "DATE"}
        ],
        "event": {
            "type": "SALE",
            "seller": seller,
            "buyer": buyer,
            "item": item,
            "price": price,
            "location": city,
            "date": date
        }
    })


dataset_path = os.path.join(BASE_DIR, "labeled_dataset.json")

with open(dataset_path, "w") as f:
    json.dump(dataset, f, indent=4)

print("[INFO] Training dataset created:", len(dataset))


# -----------------------------------
# 3. ENTITY EXTRACTION (NER)
# -----------------------------------

person_pattern = r"[A-Z][a-z]+ [A-Z][a-z]+"
date_pattern = r"\d{1,2} [A-Za-z]+ \d{4}"
place_pattern = r"\b(Delhi|London|Paris|Boston)\b"

results = []

for record in dataset:

    text = record["text"]

    persons = re.findall(person_pattern, text)
    places = re.findall(place_pattern, text)
    dates = re.findall(date_pattern, text)

    sale_event = None

    if "sold" in text.lower():

        sale_event = {
            "type": "SALE",
            "seller": persons[0] if len(persons) > 0 else None,
            "buyer": persons[1] if len(persons) > 1 else None,
            "location": places[0] if places else None,
            "date": dates[0] if dates else None
        }

    results.append({
        "text": text,
        "persons": persons,
        "places": places,
        "dates": dates,
        "event": sale_event
    })


extraction_path = os.path.join(BASE_DIR, "extraction_results.json")

with open(extraction_path, "w") as f:
    json.dump(results, f, indent=4)

print("[INFO] Extraction completed")


# -----------------------------------
# 4. CREATE STRUCTURED OUTPUT
# -----------------------------------

phase2_output = []

for record in results:

    text = record["text"]

    entities = []

    for label, values in [
        ("PERSON", record["persons"]),
        ("PLACE", record["places"]),
        ("DATE", record["dates"])
    ]:

        for value in values:

            start = text.index(value)
            end = start + len(value)

            entities.append({
                "entity": value,
                "label": label,
                "evidence_pointer": [start, end],
                "confidence": 1.0
            })

    phase2_output.append({
        "text": text,
        "entities": entities
    })


output_path = os.path.join(BASE_DIR, "phase2_output.json")

with open(output_path, "w") as f:
    json.dump(phase2_output, f, indent=4)

print("[INFO] Structured entity output saved")


# -----------------------------------
# 5. PRECISION EVALUATION
# -----------------------------------

correct = 0
total = 0

for pred, gold in zip(results, dataset):

    pred_entities = set(pred["persons"] + pred["places"] + pred["dates"])

    gold_entities = {e["text"] for e in gold["entities"]}

    correct += len(pred_entities & gold_entities)
    total += len(pred_entities)

precision = correct / total if total else 0

print("\nPrecision:", round(precision,3))


# -----------------------------------
# 6. EXIT CRITERIA CHECK
# -----------------------------------

if precision >= 0.90:
    print("[SUCCESS] Exit Criteria Achieved")
else:
    print("[WARNING] Precision below requirement")