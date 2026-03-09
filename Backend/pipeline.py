import os
import json
import requests
import time


from Phase1.document import extract_and_save_data
from Phase2.entity_extraction import main as run_phase2
from Phase3.normalize import main as run_phase3

BASE_URL = "http://127.0.0.1:8000/api/v1"

def process_document_end_to_end(image_path: str):
    print("\n" + "="*50)
    print(f"STARTING DIRP AUTOMATED PIPELINE")
    print("="*50)
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Cannot find image at {image_path}")
        return False

    start_time = time.time()

   
    print("\n[STEP 1/4] Running Phase 1: Mistral OCR...")
    extract_and_save_data(image_path)

    
    print("\n[STEP 2/4] Running Phase 2: Gemini Entity Extraction...")
    run_phase2()

    
    print("\n[STEP 3/4] Running Phase 3: AI Normalization & Embeddings...")
    run_phase3()

   
    print("\n[STEP 4/4] Pushing to Phase 4: Identity Graph Database...")
    
    try:
        with open("Phase3/phase3_output.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[ERROR] Pipeline failed before reaching Phase 3 output.")
        return False

    payload = []
    for i, ent in enumerate(data.get("entities", [])):
        if ent.get("label") == "PERSON":
            norm_data = ent.get("normalized_data", {})
            node = {
                "node_id": f"doc_entity_{int(time.time())}_{i}", 
                "label": "PERSON",
                "normalized_data": {
                    "standardized_name": norm_data.get("standardized_name"),
                    "phonetic_key": norm_data.get("phonetic_key"),
                    "embedding": norm_data.get("embedding"),
                    "date_start": None, 
                    "normalized_place": None,
                    "owner": None,
                    "plantation": None
                },
                "evidence": [{
                    "document_id": os.path.basename(image_path),
                    "extracted_text": ent.get("entity", ""),
                    "character_offsets": [0, len(ent.get("entity", ""))],
                    "bounding_box": [[0,0], [0,0], [0,0], [0,0]] 
                }]
            }
            payload.append(node)

    if not payload:
        print("[WARNING] No PERSON entities found in document to ingest.")
        return True

    
    try:
        res1 = requests.post(f"{BASE_URL}/graph/ingest", json=payload)
        print(f"[API] Ingest Response: {res1.json().get('message', 'Success')}")

        res2 = requests.post(f"{BASE_URL}/graph/resolve")
        print(f"[API] AI Resolution: Generated {res2.json().get('hypotheses_generated', 0)} new match hypotheses.")
    except requests.exceptions.ConnectionError:
        print("[ERROR] FastAPI server is not running. Start it with 'uvicorn main:app --reload'")
        return False

    end_time = time.time()
    print("\n" + "="*50)
    print(f"PIPELINE COMPLETE in {round(end_time - start_time, 2)} seconds!")
    print("Data is now available in the Neo4j Review Queue.")
    print("="*50 + "\n")
    return True

if __name__ == "__main__":
    target_image = "C:\\Users\\Ruturaj\\Downloads\\Try2.jpg"
    process_document_end_to_end(target_image)