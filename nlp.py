from transformers import pipeline

# Download and cache the NER pipeline from Hugging Face
ner = pipeline("ner", grouped_entities=True)

def extract_comparator_info(text):
    """
    Use a simple NER pipeline to try and extract interventions and outcomes.
    (Stub for now; will improve with real patterns/models.)
    """
    if not text:
        return {}
    entities = ner(text)
    # You can improve this logic to look for DRUG, DISEASE, or other entity types
    return entities
