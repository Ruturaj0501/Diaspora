import json
import os
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()  




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
    print("[INFO] Initializing Gemini client...")
    
    client = genai.Client()
    
    print("[INFO] Calling Gemini 2.5 Flash for structured extraction...")
    
    prompt = f"""
    You are an AI processing historical documents for the Diaspora Identity Reconstruction Program (DIRP). 
    Extract the core entities and events from the following text based strictly on the provided schema.
    
    Target Entity Types: PERSON, PLACE, DATE, OWNERSHIP.
    Target Event Types: Sale/Transfer (look for keywords like sold, purchased, conveyed, etc.).
    
    For every extracted item, provide a field-level confidence score (0.0 to 1.0) and the exact character 
    evidence pointers [start_index, end_index] mapping back to the original text.
    
    Source Text:
    {text}
    """
    
   
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentExtraction,
            temperature=0.1,
        ),
    )
    
    return response.text

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
    
    
    json_result_str = extract_structured_data(text)
    
   
    try:
        extracted_data = json.loads(json_result_str)
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse the JSON response from Gemini.")
        return

    
    final_output = {
        "text": text,
        "entities": extracted_data.get("entities", []),
        "events": extracted_data.get("events", [])
    }

   
    with open("Phase2/phase2_output.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    print("\n[SUCCESS] Phase 2 completed.")
    print(f"[SUCCESS] Extracted {len(final_output['entities'])} entities and {len(final_output['events'])} events.")
    print("[SUCCESS] Output saved to Phase2/phase2_output.json")

if __name__ == "__main__":
    main()