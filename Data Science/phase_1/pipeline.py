import json
import random
from collections import defaultdict
import os


# -----------------------------------
# 1. CREATE GOLD DATASET
# -----------------------------------

doc_types = ["ledger", "probate_inventory", "bill_of_sale"]

names = ["John Smith", "William Brown", "Henry Walker", "Samuel Adams"]
cities = ["Delhi", "London", "Boston", "Paris"]
items = ["horse", "wagon", "cotton", "land", "furniture"]


gold_dataset = []

for i in range(500):

    doc_type = random.choice(doc_types)

    seller = random.choice(names)
    buyer = random.choice(names)
    item = random.choice(items)
    city = random.choice(cities)
    amount = random.randint(10, 500)

    text = f"{seller} sold {item} to {buyer} in {city} for {amount} dollars"

    rows = [
        {
            "seller": seller,
            "buyer": buyer,
            "item": item,
            "price": amount,
            "location": city
        }
    ]

    gold_dataset.append({
        "doc_id": i+1,
        "document_type": doc_type,
        "text": text,
        "rows": rows
    })



os.makedirs("Data_science/phase_1", exist_ok=True)
with open("Data_science/phase_1/gold_dataset_500.json", "w") as f:
    json.dump(gold_dataset, f, indent=4)

print("Gold dataset created:", len(gold_dataset))


# -----------------------------------
# 2. SIMULATE OCR PREDICTIONS
# -----------------------------------

predictions = []

for record in gold_dataset:

    text = record["text"]

    # simulate OCR error
    if random.random() < 0.15:
        text = text.replace("sold", "sol")

    predictions.append({
        "doc_id": record["doc_id"],
        "document_type": record["document_type"],
        "predicted_text": text,
        "predicted_rows": record["rows"]
    })

os.makedirs("Data_science/phase_1", exist_ok=True)
with open("Data_science/phase_1/predictions.json", "w") as f:
    json.dump(predictions, f, indent=4)


# -----------------------------------
# 3. CER FUNCTION
# -----------------------------------

def cer(ref, hyp):

    ref = list(ref)
    hyp = list(hyp)

    dp = [[0]*(len(hyp)+1) for _ in range(len(ref)+1)]

    for i in range(len(ref)+1):
        dp[i][0] = i

    for j in range(len(hyp)+1):
        dp[0][j] = j

    for i in range(1, len(ref)+1):
        for j in range(1, len(hyp)+1):

            if ref[i-1] == hyp[j-1]:
                cost = 0
            else:
                cost = 1

            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )

    return dp[len(ref)][len(hyp)] / len(ref)


# -----------------------------------
# 4. WER FUNCTION
# -----------------------------------

def wer(ref, hyp):

    ref = ref.split()
    hyp = hyp.split()

    dp = [[0]*(len(hyp)+1) for _ in range(len(ref)+1)]

    for i in range(len(ref)+1):
        dp[i][0] = i

    for j in range(len(hyp)+1):
        dp[0][j] = j

    for i in range(1, len(ref)+1):
        for j in range(1, len(hyp)+1):

            if ref[i-1] == hyp[j-1]:
                cost = 0
            else:
                cost = 1

            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )

    return dp[len(ref)][len(hyp)] / len(ref)


# -----------------------------------
# 5. METRICS DASHBOARD
# -----------------------------------

cer_scores = defaultdict(list)
wer_scores = defaultdict(list)

table_correct = 0
table_total = 0


for gold, pred in zip(gold_dataset, predictions):

    doc_type = gold["document_type"]

    cer_scores[doc_type].append(cer(gold["text"], pred["predicted_text"]))
    wer_scores[doc_type].append(wer(gold["text"], pred["predicted_text"]))

    if gold["rows"] == pred["predicted_rows"]:
        table_correct += 1

    table_total += 1


print("\nMetrics Dashboard\n")

for doc in doc_types:

    avg_cer = sum(cer_scores[doc]) / len(cer_scores[doc])
    avg_wer = sum(wer_scores[doc]) / len(wer_scores[doc])

    print(doc)
    print("CER:", round(avg_cer,3))
    print("WER:", round(avg_wer,3))
    print()


table_accuracy = table_correct / table_total

print("Table Extraction Accuracy:", round(table_accuracy,3))


# -----------------------------------
# 6. EXIT CRITERIA
# -----------------------------------

usable_extraction = 1 - sum(sum(v) for v in cer_scores.values()) / 500

print("\nUsable Extraction:", round(usable_extraction,3))

if usable_extraction >= 0.85:
    print("Exit Criteria Achieved")
else:
    print("Exit Criteria NOT Achieved")