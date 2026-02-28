import json
from normalize import normalize_place

with open("phase_3/ground_truth.json") as f:
    data = json.load(f)

correct = 0
total = len(data)

for item in data:

    pred = normalize_place(item["text"])

    if pred == item["expected"]:
        correct += 1

    print(item["text"], "->", pred)

accuracy = correct / total

print("\nAccuracy:", round(accuracy * 100, 2), "%")
print(f"{correct}/{total} correct")