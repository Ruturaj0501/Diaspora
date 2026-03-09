import json
from pathlib import Path
from datetime import datetime
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

PHASE2_PATH = Path("Phase2/phase2_output.json")
OUTPUT_DIR = Path("Phase5")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "output_report.json"

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)


def load_records():
    if not PHASE2_PATH.exists():
        print("[ERROR] Phase2 output file not found.")
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
        text = r.get("text", "")
        entities = r.get("entities", [])
        events = r.get("events", [])

        entity_strings = []
        for e in entities:
            ent_text = e.get("entity", "Unknown")
            label = e.get("label", "Unknown")

            pointers = e.get("evidence_pointer", [])
            start = pointers[0] if len(pointers) > 0 else 0
            end = pointers[1] if len(pointers) > 1 else start

            conf = e.get("confidence", 0)

            entity_strings.append(
                f"- {ent_text} ({label}) | Chars: {start} to {end} | Conf: {conf}"
            )

        entities_formatted = "\n".join(entity_strings) if entity_strings else "No entities extracted."

        event_strings = []
        for evt in events:
            evt_type = evt.get("event_type", "Unknown")
            trigger = evt.get("trigger_word", "Unknown")

            pointers = evt.get("evidence_pointer", [])
            start = pointers[0] if len(pointers) > 0 else 0
            end = pointers[1] if len(pointers) > 1 else start

            event_strings.append(
                f"- Event: {evt_type} | Trigger Word: '{trigger}' | Chars: {start} to {end}"
            )

        events_formatted = "\n".join(event_strings) if event_strings else "No structured events extracted."

        block = f"""
Evidence [{idx}]
Source Text: {text}

Extracted Entities:
{entities_formatted}

Extracted Events (Relationships/Transfers):
{events_formatted}
"""

        context_blocks.append(block)

        structured_evidence.append({
            "evidence_id": idx,
            "text": text,
            "entities": entities,
            "events": events
        })

    return "\n".join(context_blocks), structured_evidence


def generate_report(question, context):

    prompt = f"""
You are a STRICT historical research copilot for the DIRP architecture.

RULES:
- Use ONLY the evidence provided below. If the answer is not there, state "No evidence found."
- Every factual statement MUST be cited inline like [1], [2] pointing to the Evidence ID.
- Do NOT invent document IDs, dates, or names.
- Pay special attention to "Extracted Events" to answer questions about relationships or transfers of ownership.

QUESTION:
{question}

EVIDENCE:
{context}

OUTPUT FORMAT EXACTLY:

Narrative Summary:
(Write your grounded answer here with inline citations like [1])

Footnotes:
[1] (List the entities, events, and character pointers used to make this claim)

Next Best Actions:
(Analyze the evidence for missing historical gaps—like missing dates, locations, or ownership transfers. Suggest 2 specific record types the researcher should look for next to fill these gaps).
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    return completion.choices[0].message.content


def save_output(question, narrative, evidence_list):
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "narrative_summary": narrative,
        "footnotes": evidence_list
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

    print(f"\n[SUCCESS] Output saved to: {OUTPUT_FILE}")


def copilot():
    print("=== DIRP Research Copilot (Phase 5 - Groq Llama Mode) ===")

    records = load_records()

    if not records:
        print("No Phase 2 records found.")
        return

    while True:
        question = input("\nAsk a historical question (or type 'exit'): ")

        if question.lower() == "exit":
            print("Exiting Copilot.")
            break

        results = retrieve(question, records)

        if not results:
            print("No high-confidence evidence found. Try a different query.")
            continue

        context, structured_evidence = build_context(results)

        print("\n[INFO] Generating report via Groq Llama 3...")
        narrative = generate_report(question, context)

        print("\n" + "="*50)
        print(" GROUNDED REPORT ")
        print("="*50)
        print(narrative)
        print("="*50)

        save_output(question, narrative, structured_evidence)


if __name__ == "__main__":
    copilot()