import json
from pathlib import Path

DATA_PATH = Path("phase2_output.json")


def load_records():
    if not DATA_PATH.exists():
        print("No extracted data found.")
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    return data


def search_records(query, records):
    query = query.lower()
    results = []

    for r in records:
        text = r.get("text", "").lower()

        if query in text:
            results.append(r)

    return results


def recommend_next_steps():
    return [
        "Search birth records",
        "Search death records",
        "Search census / migration data",
    ]


def copilot():
    print("DIRP Research Copilot")

    records = load_records()

    if not records:
        print("No extracted data found.")
        return

    while True:
        query = input("\nAsk a historical question (or type exit): ")

        if query.lower() == "exit":
            break

        results = search_records(query, records)

        if not results:
            print("No evidence found.")
        else:
            print("\nEvidence Found:\n")

            for r in results:
                print("-", r["text"])

                if "events" in r:
                    for e in r["events"]:
                        print("  Event:", e["event"])
                        print("  Date:", ", ".join(e.get("date", [])))
                        print("  Location:", ", ".join(e.get("location", [])))

        print("\nNext Best Actions")
        for step in recommend_next_steps():
            print("•", step)


if __name__ == "__main__":
    copilot()
