import spacy
import json

nlp = spacy.load("en_core_web_sm")


def extract_entities(text):

    doc = nlp(text)

    data = {
        "person": None,
        "location": None,
        "year": None
    }

    for ent in doc.ents:

        if ent.label_ == "PERSON":
            data["person"] = ent.text

        if ent.label_ == "GPE":
            data["location"] = ent.text

        if ent.label_ == "DATE":
            data["year"] = ent.text

    return data


def process_documents(documents):

    results = []

    for text in documents:
        entities = extract_entities(text)

        results.append({
            "text": text,
            "entities": entities
        })

    return results


# MAIN EXECUTION
if __name__ == "__main__":

    sample_documents = [
        "Isaac was sold to John Brown in Virginia in 1856.",
        "Mary was born in North Carolina in 1820.",
        "Samuel died in Texas in 1871."
    ]

    output = process_documents(sample_documents)

    print(json.dumps(output, indent=4))

    with open("phase2_output.json", "w") as f:
        json.dump(output, f, indent=4)