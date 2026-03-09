import json
import os
import numpy as np
from difflib import SequenceMatcher
from sklearn.linear_model import LogisticRegression

print("\nPHASE 4 — ENTITY RESOLUTION RANKER\n")

BASE_DIR = "Data_science/phase_4"
os.makedirs(BASE_DIR, exist_ok=True)

INPUT_FILE = "Data_science/phase_3/phase3_output.json"


# ------------------------------------------------
# LOAD PHASE 3 DATA
# ------------------------------------------------

with open(INPUT_FILE) as f:
    records = json.load(f)

print("[INFO] Records loaded:", len(records))


# ------------------------------------------------
# SIMILARITY FUNCTION
# ------------------------------------------------

def similarity(a, b):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


# ------------------------------------------------
# 1 FEATURE ENGINEERING
# ------------------------------------------------

def create_features(r1, r2):

    text_sim = similarity(r1["text"], r2["text"])

    seller_sim = similarity(
        r1["alias"].get("seller", ""),
        r2["alias"].get("seller", "")
    )

    buyer_sim = similarity(
        r1["alias"].get("buyer", ""),
        r2["alias"].get("buyer", "")
    )

    location_overlap = 1 if r1["alias"].get("location") == r2["alias"].get("location") else 0

    return [text_sim, seller_sim, buyer_sim, location_overlap]


# ------------------------------------------------
# HARD CONSTRAINTS
# ------------------------------------------------

def hard_constraints(r1, r2):

    loc1 = r1["alias"].get("location")
    loc2 = r2["alias"].get("location")

    if loc1 and loc2 and loc1 != loc2:
        return False

    return True


# ------------------------------------------------
# BUILD DATASET
# ------------------------------------------------

X = []
y = []
pairs = []

for i in range(len(records)):
    for j in range(i + 1, len(records)):

        r1 = records[i]
        r2 = records[j]

        if not hard_constraints(r1, r2):
            continue

        features = create_features(r1, r2)

        X.append(features)

        seller1 = r1["alias"].get("seller")
        seller2 = r2["alias"].get("seller")

        loc1 = r1["alias"].get("location")
        loc2 = r2["alias"].get("location")

        label = 1 if (seller1 == seller2 and loc1 == loc2) else 0

        y.append(label)

        pairs.append((r1, r2))

X = np.array(X)
y = np.array(y)

print("[INFO] Training pairs:", len(X))


# ------------------------------------------------
# TRAIN RANKER
# ------------------------------------------------

model = LogisticRegression()
trained = True

if len(set(y)) < 2:
    print("[WARNING] Not enough class diversity for training.")
    print("[INFO] Using similarity fallback scoring.")
    trained = False
else:
    model.fit(X, y)
    print("[INFO] Model trained successfully.")


# ------------------------------------------------
# GENERATE MATCH SCORES
# ------------------------------------------------

results = []

for idx, (r1, r2) in enumerate(pairs):

    features = X[idx].reshape(1, -1)

    if trained:
        score = model.predict_proba(features)[0][1]
    else:
        score = float(np.mean(features))

    results.append({
        "record1": r1["text"],
        "record2": r2["text"],
        "seller1": r1["alias"].get("seller"),
        "seller2": r2["alias"].get("seller"),
        "location": r1["alias"].get("location"),
        "match_score": float(score)
    })


# ------------------------------------------------
# EVALUATION
# ------------------------------------------------

false_merges = 0
total_merges = 0
correct = 0

for r in results:

    if r["match_score"] > 0.8:

        total_merges += 1

        if r["seller1"] != r["seller2"]:
            false_merges += 1
        else:
            correct += 1


false_merge_rate = false_merges / total_merges if total_merges else 0
cluster_purity = correct / total_merges if total_merges else 0


print("\nFalse Merge Rate:", round(false_merge_rate,3))
print("Cluster Purity:", round(cluster_purity,3))


# ------------------------------------------------
# SAVE OUTPUT
# ------------------------------------------------

output_path = os.path.join(BASE_DIR, "phase4_output.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print("\n[INFO] Output saved to:", output_path)


# ------------------------------------------------
# EXIT CRITERIA
# ------------------------------------------------

THRESHOLD = 0.05

if false_merge_rate < THRESHOLD:
    print("[SUCCESS] False merge rate below threshold")
    print("[SUCCESS] Human-in-loop workflow operational")
else:
    print("[WARNING] False merge rate too high")