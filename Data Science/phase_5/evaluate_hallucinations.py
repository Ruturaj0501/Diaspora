import json
import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

REPORT_PATH = "Phase5/output_report.json"

def evaluate_hallucination():
    print("=== DIRP Hallucination Evaluator ===")
    
    if not os.path.exists(REPORT_PATH):
        print("[ERROR] No report found. Run copilot.py first.")
        return

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    narrative = report_data.get("narrative_summary", "")
    evidence_list = report_data.get("footnotes", [])
    
    
    allowed_facts = []
    for ev in evidence_list:
        allowed_facts.append(ev.get("text", ""))
        for ent in ev.get("entities", []):
            allowed_facts.append(ent.get("entity", ""))
            
    allowed_context = "\n".join(allowed_facts)

    print("[INFO] Submitting Narrative and Evidence to Mistral Judge...")
    
    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)

    prompt = f"""
    You are a strict data-validation judge. 
    Compare the Generated Narrative against the Allowed Evidence.
    
    ALLOWED EVIDENCE:
    {allowed_context}
    
    GENERATED NARRATIVE:
    {narrative}
    
    TASK:
    Identify ANY names, dates, places, or historical facts in the Narrative that DO NOT exist in the Allowed Evidence.
    
    Respond strictly in JSON:
    {{
        "hallucination_count": 0,
        "invented_facts": []
    }}
    """

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    result = json.loads(response.choices[0].message.content)
    
    count = result.get("hallucination_count", 0)
    
    print("\n" + "="*50)
    print(" EVALUATION RESULTS ")
    print("="*50)
    if count == 0:
        print("PASSED: Hallucination Rate is 0.0%. All facts are perfectly grounded.")
    else:
        print(f"FAILED: Detected {count} hallucinated facts!")
        for fact in result.get("invented_facts", []):
            print(f"   - {fact}")
    print("="*50)

if __name__ == "__main__":
    evaluate_hallucination()