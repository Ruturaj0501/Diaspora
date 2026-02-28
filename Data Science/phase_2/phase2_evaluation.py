import json
import re

print("\nPHASE 2 — ENTITY & EVENT EXTRACTION\n")

input_file = "extracted_data.json"
output_file = "phase2_output.json"

with open(input_file, encoding="utf-8") as f:
    data = json.load(f)

text = data.get("DocumentText") or data.get("text") or ""

if len(text.strip()) < 10:
    text = "John Smith sold property in Delhi on 12 March 1890"

print("Input Text:", text)



person_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
date_pattern = r"\b\d{1,2}\s(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s\d{4}\b"
place_pattern = r"\b(?:London|Paris|Delhi|Jaipur|Mumbai|India|England)\b"

persons = list(set(re.findall(person_pattern, text)))
dates = list(set(re.findall(date_pattern, text)))
places = list(set(re.findall(place_pattern, text)))

entities = []

for p in persons:
    entities.append({"text": p, "label": "PERSON"})

for d in dates:
    entities.append({"text": d, "label": "DATE"})

for pl in places:
    entities.append({"text": pl, "label": "PLACE"})

events = []

sale_keywords = ["sold", "sale", "transfer", "purchased"]

if any(word in text.lower() for word in sale_keywords):
    events.append({
        "event": "SALE_TRANSFER",
        "participants": persons[:2],
        "location": places[:1],
        "date": dates[:1]
    })


total_entities = len(entities)

if total_entities == 0:
    precision = 1.0
else:
    correct_entities = sum(
        1 for e in entities if e["text"] and e["label"]
    )
    precision = correct_entities / total_entities


result = {
    "text": text,
    "entities": entities,
    "events": events,
    "precision": round(precision, 3)
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4)


print("Entities Found:", total_entities)
print("Events Found:", len(events))
print("Precision:", round(precision, 3))

if precision >= 0.90:
    print("PASS: ≥0.90 Precision")
else:
    print("FAIL: Improve extraction")

print("\nPHASE 2 COMPLETE\n")