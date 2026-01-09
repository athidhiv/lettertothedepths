import joblib
import numpy as np
from gensim.models import Word2Vec

# 1. Load the models
w2v_model = Word2Vec.load("word2vec_model.model")
classifier = joblib.load("toxic_classifier.pkl")

def get_sentence_vector(text):
    words = text.lower().split()
    # Average the vectors of words found in the vocabulary
    vectors = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if vectors:
        return np.mean(vectors, axis=0).reshape(1, -1)
    else:
        return np.zeros((1, w2v_model.vector_size))

def test_letter(text):
    # Vectorize -> Predict
    vector = get_sentence_vector(text)
    prediction = classifier.predict(vector)[0]
    prob = classifier.predict_proba(vector)[0]
    
    status = "🚩 HARMFUL" if prediction == 1 else "✅ SAFE"
    conf = prob[1] if prediction == 1 else prob[0]
    
    print(f"Letter: '{text}'\nResult: {status} ({conf*100:.2f}%)\n")

# Test locally
test_letter("I love the backwaters in Kochi, so peaceful.")
test_letter("I am going to hurt you if I find you bitch.")
test_letter("This traffic is absolute trash, I hate everyone here.")
test_letter("I love killing and torturing people.")
test_letter("i love cunty bitches")