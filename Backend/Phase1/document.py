import json
from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()


class LayoutBlock(BaseModel):
    text: str = Field(description="The transcribed text of the row, paragraph, or block.")
    box_2d: list[int] = Field(description="Bounding box [ymin, xmin, ymax, xmax] normalized to 1000.")

class DocumentExtraction(BaseModel):
    DocumentText: str = Field(description="The full continuous transcription of the document.")
    LayoutBlocks: list[LayoutBlock]


def extract_and_save_data(image_path, output_json="Phase1/extracted_data.json"):
    print("[INFO] Initializing Gemini client...")
    client = genai.Client()

    print(f"[INFO] Processing image: {image_path}")
    try:
        img = Image.open(image_path)
        img_width, img_height = img.size
    except Exception as e:
        raise ValueError(f"Could not open image. Ensure the path is correct: {e}")

    prompt = """
    Transcribe this historical document accurately. 
    1. Provide the full transcription in DocumentText.
    2. Break the document down into logical LayoutBlocks (rows, lines, or paragraphs). 
    3. For each block, provide the text and the bounding box in [ymin, xmin, ymax, xmax] format scaled to 1000.
    """

    print("[INFO] Sending image to Gemini Flash (this may take a few seconds)...")
    response = client.models.generate_content(
        model='gemini-flash-latest', 
        contents=[img, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentExtraction,
            temperature=0.1, 
        ),
    )

    raw_data = json.loads(response.text)
    document_text = raw_data.get("DocumentText", "")
    layout_blocks = []

    print("\n--- Parsing Gemini OCR Results ---")
    for block in raw_data.get("LayoutBlocks", []):
        text = block["text"]
        
        ymin, xmin, ymax, xmax = block["box_2d"]
        
        px_xmin = int((xmin / 1000.0) * img_width)
        px_xmax = int((xmax / 1000.0) * img_width)
        px_ymin = int((ymin / 1000.0) * img_height)
        px_ymax = int((ymax / 1000.0) * img_height)
        
        clean_bbox = [
            [px_xmin, px_ymin],
            [px_xmax, px_ymin],
            [px_xmax, px_ymax],
            [px_xmin, px_ymax]
        ]
        
        layout_blocks.append({
            "text": text,
            "coordinates": clean_bbox,
            "confidence": "N/A" 
        })
        print(f"Extracted: '{text}'")

    final_output = {
        "DocumentText": document_text,
        "LayoutBlocks": layout_blocks
    }
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)
        
    print(f"\n[SUCCESS] Extracted {len(layout_blocks)} text blocks.")
    print(f"[SUCCESS] Data successfully saved to {output_json}")
        
    return final_output

if __name__ == "__main__":
    
    image_file = "C:\\Users\\Ruturaj\\Downloads\\Try2.jpg"
    
    try:
        extract_and_save_data(image_file)
    except Exception as e:
        print(f"An error occurred: {e}")