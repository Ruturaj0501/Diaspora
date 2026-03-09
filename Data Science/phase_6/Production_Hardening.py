import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# -------------------------------
# Load / Save JSON
# -------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# -------------------------------
# Drift Monitoring
# -------------------------------

def drift_monitoring(data, threshold=0.75):

    embeddings = []
    drift_cases = []

    for record in data:

        emb = record.get("embedding")

        if emb is None:
            continue

        emb = np.array(emb).reshape(1, -1)

        if len(embeddings) == 0:
            embeddings.append(emb)
            continue

        similarities = cosine_similarity(emb, np.vstack(embeddings))[0]

        avg_similarity = float(np.mean(similarities))

        if avg_similarity < threshold:

            drift_cases.append({
                "text": record.get("text"),
                "similarity_score": avg_similarity,
                "alert": "New document type detected"
            })

        embeddings.append(emb)

    return drift_cases


# -------------------------------
# Active Learning Loop
# -------------------------------

def active_learning(data, confidence_threshold=0.65):

    labeling_queue = []

    for record in data:

        confidence = record.get("confidence", 1)

        if confidence < confidence_threshold:

            labeling_queue.append({
                "text": record.get("text"),
                "prediction": record.get("alias"),
                "confidence": confidence,
                "status": "Needs manual labeling"
            })

    return labeling_queue


# -------------------------------
# Main Pipeline
# -------------------------------

def main():

    phase3_file = "Data_science/phase_3/phase3_output.json"
    output_file = "Data_science/phase_6/phase6_datascience_output.json"

    if not os.path.exists(phase3_file):
        print("❌ Phase 3 output not found")
        return

    print("Loading Phase 3 output...")

    data = load_json(phase3_file)

    print("Records loaded:", len(data))

    print("Running Drift Monitoring...")
    drift_results = drift_monitoring(data)

    print("Running Active Learning...")
    active_learning_results = active_learning(data)

    results = {
        "drift_monitoring": drift_results,
        "active_learning_queue": active_learning_results
    }

    save_json(output_file, results)

    print("\n✅ Phase 6 Completed Successfully")
    print("Drift cases detected:", len(drift_results))
    print("Low confidence cases:", len(active_learning_results))
    print("Output saved to:", output_file)


# -------------------------------

if __name__ == "__main__":
    main()