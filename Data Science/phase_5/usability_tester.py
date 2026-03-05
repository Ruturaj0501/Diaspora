import json
import os
from datetime import datetime

REPORT_PATH = "Phase5/output_report.json"
FEEDBACK_LOG = "Phase5/researcher_feedback.json"

def run_usability_test():
    print("\n=== DIRP Researcher Usability Testing ===")
    
    if not os.path.exists(REPORT_PATH):
        print("[ERROR] No report found to review. Run copilot.py first.")
        return

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    print("\n--- AI GENERATED REPORT ---")
    print(f"Q: {report_data.get('question')}")
    print(f"A:\n{report_data.get('narrative_summary')}")
    print("---------------------------\n")

    print("RESEARCHER EVALUATION (Rate 1 to 5, where 5 is Perfect)")
    
    try:
        acc_score = int(input("1. Factual Accuracy (Did it answer the question correctly based on the text?): "))
        cite_score = int(input("2. Citation Formatting (Are the [1] footnotes clear and helpful?): "))
        action_score = int(input("3. Next Best Actions (Were the suggested next steps logical?): "))
        comments = input("4. Any additional comments or failure points? ")
    except ValueError:
        print("[ERROR] Please enter numbers for the scores.")
        return

    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "question_tested": report_data.get("question"),
        "scores": {
            "accuracy": acc_score,
            "citations": cite_score,
            "next_actions": action_score
        },
        "comments": comments
    }

    
    feedback_history = []
    if os.path.exists(FEEDBACK_LOG):
        with open(FEEDBACK_LOG, "r", encoding="utf-8") as f:
            feedback_history = json.load(f)
            
    feedback_history.append(feedback_entry)
    
    with open(FEEDBACK_LOG, "w", encoding="utf-8") as f:
        json.dump(feedback_history, f, indent=4)

    print(f"\n[SUCCESS] Feedback logged to {FEEDBACK_LOG}. Thank you for testing!")

if __name__ == "__main__":
    run_usability_test()