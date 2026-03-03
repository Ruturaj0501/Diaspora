import json
import os
from pydantic import BaseModel, Field
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()  

# -----------------------------
# PYDANTIC DATA MODELS
# -----------------------------
class Entity(BaseModel):
    entity: str = Field(description="The exact extracted text of the entity.")
    label: str = Field(description="The type of entity. Must be one of: PERSON, PLACE, DATE, OWNERSHIP.")
    evidence_pointer: list[int] = Field(description="The exact character start and end index of the entity in the source text.")
    confidence: float = Field(description="Confidence score of the extraction between 0.0 and 1.0.")

class Event(BaseModel):
    event_type: str = Field(description="The category of the event. Must be exactly: Sale/Transfer.")
    trigger_word: str = Field(description="The exact word or phrase that indicates the event.")
    evidence_pointer: list[int] = Field(description="The exact character start and end index of the trigger word in the source text.")
    confidence: float = Field(description="Confidence score of the extraction between 0.0 and 1.0.")

class DocumentExtraction(BaseModel):
    entities: list[Entity] = Field(description="List of extracted entities.")
    events: list[Event] = Field(description="List of extracted events.")


def extract_structured_data(text: str) -> str:
    print("[INFO] Initializing Mistral client...")
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment variables.")
        
    client = Mistral(api_key=api_key)
    
    print("[INFO] Calling Mistral Small for high-speed structured extraction...")
    
   
    schema_json = json.dumps(DocumentExtraction.model_json_schema(), indent=2)
    
    prompt = f"""
    You are an AI processing historical documents for the Diaspora Identity Reconstruction Program (DIRP). 
    Extract the core entities and events from the following text based strictly on the provided schema.
    
    Target Entity Types: PERSON, PLACE, DATE, OWNERSHIP.
    Target Event Types: Sale/Transfer (look for keywords like sold, purchased, conveyed, etc.).
    
    For every extracted item, provide a field-level confidence score (0.0 to 1.0) and the exact character 
    evidence pointers [start_index, end_index] mapping back to the original text.
    
    You MUST return the output as a strictly valid JSON object exactly matching this JSON schema:
    {schema_json}

    Source Text:
    {text}
    """
    
   
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    return response.choices[0].message.content

def main():
    print("[INFO] Loading Phase 1 extracted data...")
    try:
        with open("Phase1/extracted_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[ERROR] Phase1/extracted_data.json not found. Run Phase 1 first.")
        return

    text = data.get("DocumentText", "")
    if not text:
        print("[ERROR] No 'DocumentText' found in the input JSON.")
        return

    print("[INFO] Running Entity and Event Extraction...")
    
    try:
        json_result_str = extract_structured_data(text)
        
        
        extracted_data = DocumentExtraction.model_validate_json(json_result_str)
        
    except Exception as e:
        print(f"[ERROR] Pydantic Validation or API call failed: {e}")
        return

    
    final_output = {
        "text": text,
        "entities": [ent.model_dump() for ent in extracted_data.entities],
        "events": [evt.model_dump() for evt in extracted_data.events]
    }

    
    os.makedirs("Phase2", exist_ok=True)
    
    with open("Phase2/phase2_output.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    print("\n[SUCCESS] Phase 2 completed.")
    print(f"[SUCCESS] Extracted {len(final_output['entities'])} entities and {len(final_output['events'])} events.")
    print("[SUCCESS] Output saved to Phase2/phase2_output.json")

if __name__ == "__main__":
    main()
