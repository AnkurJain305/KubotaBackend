import json

def parse_embedding_text(embedding_text):
    """Convert text embedding to list of floats"""
    if not embedding_text or embedding_text.strip() == '':
        return None

    try:
        if embedding_text.startswith('[') and embedding_text.endswith(']'):
            embedding_list = json.loads(embedding_text)
            embedding_floats = [float(x) for x in embedding_list]
            return embedding_floats
        else:
            print(f"Unexpected embedding format: {embedding_text[:50]}...")
            return None
    except Exception as e:
        print(f" Error parsing embedding: {e}")
        return None