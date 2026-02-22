import easyocr

def extract_text(image_path):
   
    print("Loading models into memory...")
    reader = easyocr.Reader(['en'], gpu=True) 

   
    print(f"Processing image: {image_path}")
    results = reader.readtext(image_path)

    print("\n--- OCR Results ---")
    for (bbox, text, prob) in results:
        print(f"Text: '{text}'")
        print(f"Confidence: {prob:.4f}")
        print(f"Bounding Box: {bbox}\n")
        
    return results

if __name__ == "__main__":

    image_file = 'C:\\Users\\Ruturaj\\Downloads\\Happy.jpeg' 
    
    try:
        extract_text(image_file)
    except Exception as e:
        print(f"An error occurred: {e}")