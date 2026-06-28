from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    embedding = model.encode(text)
    return embedding.tolist()

def cosine_similarity(vec1,vec2):
        a=np.array(vec1)
        b=np.array(vec2)
        return float(np.dot(a,b) /(np.linalg.norm(a) * np.linalg.norm(b)))

