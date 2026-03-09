import json
import os
import base64
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

def extract_and_save_data(image_path, output_json="Phase1/extracted_data.json"):
    print("[INFO] Initializing Mistral AI client...")
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment variables.")
        
    client = Mistral(api_key=api_key)

    print(f"[INFO] Processing image: {image_path}")
    if not os.path.exists(image_path):
        raise ValueError(f"Could not find image at path: {image_path}")

    # Encode the image to base64 for the Mistral API
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    print("[INFO] Sending image to Mistral OCR (mistral-ocr-latest)...")
    
    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "image_url",
            # Assuming a .jpg input based on your previous Try2.jpg file
            "image_url": f"data:image/jpeg;base64,{base64_image}"
        }
    )

    layout_blocks = []
    full_text = ""

    print("\n--- Parsing Mistral OCR Results ---")
    
    # Mistral returns data page by page as raw Markdown
    for page in response.pages:
        markdown_text = page.markdown
        full_text += markdown_text + "\n"
        
        # Because Mistral doesn't give text bounding boxes, we split by double newlines 
        # to simulate "paragraphs" and hardcode a dummy bounding box so Phase 2 doesn't crash.
        paragraphs = markdown_text.split("\n\n")
        
        for para in paragraphs:
            para = para.strip()
            if para:
                layout_blocks.append({
                    "text": para,
                    "coordinates": [[0,0], [0,0], [0,0], [0,0]], # DUMMY BOXES
                    "confidence": 1.0 
                })
                print(f"Extracted: '{para[:60]}...'")

    final_output = {
        "DocumentText": full_text.strip(),
        "LayoutBlocks": layout_blocks
    }
    
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)
        
    print(f"\n[SUCCESS] Extracted {len(layout_blocks)} text blocks.")
    print(f"[WARNING] Bounding boxes are mocked because Mistral OCR outputs pure Markdown.")
    print(f"[SUCCESS] Data successfully saved to {output_json}")
        
    return final_output

if __name__ == "__main__":
    image_file = "C:\\Users\\Ruturaj\\Downloads\\Try2.jpg"
    
    try:
        extract_and_save_data(image_file)
    except Exception as e:
        print(f"An error occurred: {e}")
