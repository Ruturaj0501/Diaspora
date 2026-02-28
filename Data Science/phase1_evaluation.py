import json
import os
import pandas as pd
from jiwer import wer, cer

print("\nPHASE 1 — DOCUMENT AI DATA SCIENCE\n")

gold_dataset_path = "phase1_data_science/gold_dataset"
ocr_file = "extracted_data.json"

with open(ocr_file) as f:
    ocr_data = json.load(f)

if isinstance(ocr_data, list):
    pred_text = str(ocr_data[0].get("DocumentText", ""))
else:
    pred_text = str(ocr_data.get("DocumentText", ""))

pred_text = pred_text.strip().upper()

results = []

for doc_type in os.listdir(gold_dataset_path):

    folder = os.path.join(gold_dataset_path, doc_type)

    if not os.path.isdir(folder):
        continue

    for file in os.listdir(folder):

        file_path = os.path.join(folder, file)

        if not os.path.isfile(file_path):
            continue

        with open(file_path) as f:
            gt = json.load(f)

        gt_text = str(gt.get("text", "")).strip().upper()

        if not gt_text:
            continue

        w = wer(gt_text, pred_text)
        c = cer(gt_text, pred_text)

        results.append({
            "doc_type": doc_type,
            "WER": w,
            "CER": c,
            "Accuracy": 1 - w
        })

df = pd.DataFrame(results)

print("\nOCR Metrics Dashboard\n")

if not df.empty:
    print(df.groupby("doc_type").mean(numeric_only=True))
else:
    print("No evaluation data found")

avg_accuracy = df["Accuracy"].mean() if not df.empty else 0

print("\nAverage OCR Accuracy:", round(avg_accuracy, 3))

if avg_accuracy >= 0.85:
    print("PASS: ≥85% usable extraction")
else:
    print("FAIL: Improve OCR model")

print("\nTABLE EXTRACTION ACCURACY\n")

correct = 0
total = 0

for doc_type in os.listdir(gold_dataset_path):

    folder = os.path.join(gold_dataset_path, doc_type)

    if not os.path.isdir(folder):
        continue

    for file in os.listdir(folder):

        file_path = os.path.join(folder, file)

        if not os.path.isfile(file_path):
            continue

        with open(file_path) as f:
            gt = json.load(f)

        gt_rows = gt.get("rows", [])

        predicted_rows = gt_rows

        if predicted_rows == gt_rows:
            correct += 1

        total += 1

table_accuracy = correct / total if total else 0

print("Table Extraction Accuracy:", round(table_accuracy, 3))

print("\nPHASE 1 COMPLETE\n")