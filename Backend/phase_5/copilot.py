import json
from pathlib import Path
from datetime import datetime
from langchain_ollama import OllamaLLM

PHASE2_PATH = Path("Phase2/phase2_output.json")
OUTPUT_DIR = Path("phase_5")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "output_report.json"

llm = OllamaLLM(model="llama3", temperature=0)

def load_records():
    if not PHASE2_PATH.exists():
        print("Phase2 output file not found.")
        return []

    with open(PHASE2_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    return data


def retrieve(query, records, min_confidence=0.5):
    query_words = query.lower().split()
    ranked = []

    for r in records:
        text = r.get("text", "").lower()
        score = sum(word in text for word in query_words)

        if score > 0:
            entities = r.get("entities", [])
            max_conf = max(
                [e.get("confidence", 0) for e in entities],
                default=0
            )

            if max_conf >= min_confidence:
                ranked.append((score, max_conf, r))

    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [r[2] for r in ranked[:5]]

def build_context(results):
    context_blocks = []
    structured_evidence = []

    for idx, r in enumerate(results, 1):
        evidence = r.get("evidence_pointer", {})
        bbox = evidence.get("bbox", [])

        x1 = bbox[0] if len(bbox) == 4 else None
        y1 = bbox[1] if len(bbox) == 4 else None
        x2 = bbox[2] if len(bbox) == 4 else None
        y2 = bbox[3] if len(bbox) == 4 else None

        max_conf = max(
            [e.get("confidence", 0) for e in r.get("entities", [])],
            default=0
        )

        block = f"""
Evidence [{idx}]
Text: {r.get("text")}
Document ID: {evidence.get("doc_id")}
Page: {evidence.get("page")}
Pixel Coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}
Confidence: {max_conf}
"""
        context_blocks.append(block)

        structured_evidence.append({
            "evidence_id": idx,
            "text": r.get("text"),
            "doc_id": evidence.get("doc_id"),
            "page": evidence.get("page"),
            "coordinates": {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            },
            "confidence": max_conf
        })

    return "\n".join(context_blocks), structured_evidence

def generate_report(question, context):
    prompt = f"""
You are a STRICT historical research copilot.

RULES:
- Use ONLY the evidence provided.
- Do NOT invent document IDs or page numbers.
- Every factual statement MUST cite like [1], [2].
- Do NOT add extra commentary.

QUESTION:
{question}

EVIDENCE:
{context}

OUTPUT FORMAT EXACTLY:

Narrative Summary:
(write answer with inline citations like [1])

Footnotes:
[1] Document ID: ...
     Page: ...
     Pixel Coordinates: x1=..., y1=..., x2=..., y2=...
     Confidence: ...
"""

    return llm.invoke(prompt)

def save_output(question, narrative, evidence_list):

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "narrative_summary": narrative,
        "footnotes": evidence_list
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

    print(f"\nOutput saved to: {OUTPUT_FILE}")

def copilot():
    print("=== DIRP Research Copilot (Phase 5 - Grounded Mode) ===")

    records = load_records()

    if not records:
        print("No Phase 2 records found.")
        return

    while True:
        question = input("\nAsk a historical question (or type exit): ")

        if question.lower() == "exit":
            print("Exiting Copilot.")
            break

        results = retrieve(question, records)

        if not results:
            print("No high-confidence evidence found.")
            continue

        context, structured_evidence = build_context(results)

        narrative = generate_report(question, context)

        print("\n--- Grounded Report ---\n")
        print(narrative)

        save_output(question, narrative, structured_evidence)


if __name__ == "__main__":
    copilot()