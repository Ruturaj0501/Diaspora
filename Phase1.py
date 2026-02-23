import easyocr
import json

def extract_and_save_data(image_path, output_json="extracted_data.json"):
    print("[INFO] Loading EasyOCR models into memory...")
    
    reader = easyocr.Reader(['en'], gpu=True) 

    print(f"[INFO] Processing image: {image_path}")
   
    results = reader.readtext(
        image_path,
        mag_ratio=1.5,      
        adjust_contrast=0.5 
    )

    document_text = []
    layout_blocks = []

    print("\n--- Parsing OCR Results ---")
    for (bbox, text, prob) in results:
        document_text.append(text)
        
       
        clean_bbox = [[int(coord[0]), int(coord[1])] for coord in bbox]
        
        layout_blocks.append({
            "text": text,
            "coordinates": clean_bbox,
            "confidence": round(float(prob), 4)
        })
        print(f"Extracted: '{text}' (Confidence: {prob:.2f})")

   
    full_text = " ".join(document_text)

    
    final_output = {
        "DocumentText": full_text,
        "LayoutBlocks": layout_blocks
    }

    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)
        
    print(f"\n[SUCCESS] Extracted {len(layout_blocks)} text blocks.")
    print(f"[SUCCESS] Data successfully saved to {output_json}")
        
    return final_output

if __name__ == "__main__":
    
    image_file = 'C:\\Users\\Ruturaj\\Downloads\\Try1.jpg' 
    
    try:
        extract_and_save_data(image_file)
    except Exception as e:
        print(f"An error occurred: {e}")