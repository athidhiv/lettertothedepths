from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from gensim.models import Word2Vec

app = Flask(__name__)
CORS(app)  # This allows your JS to talk to the Python server

# 1. Load your models
w2v_model = Word2Vec.load("word2vec_model.model")
classifier = joblib.load("toxic_classifier.pkl")

def get_vector(text):
    words = text.lower().split()
    # Get vectors for words that exist in the vocabulary
    vectors = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if vectors:
        return np.mean(vectors, axis=0).reshape(1, -1)
    else:
        # Return zeros if no words are recognized
        return np.zeros((1, w2v_model.vector_size))

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"is_harmful": False, "confidence": 0})

    # 2. Process the text
    vector = get_vector(text)
    
    # 3. Get probability scores
    # probability[0] is index 0 (Safe), index 1 (Harmful)
    probabilities = classifier.predict_proba(vector)[0]
    harmful_prob = probabilities[1] 

    # 4. Apply your 98% strict logic
    # Only mark as harmful if the confidence is > 0.98
    is_harmful = True if harmful_prob >= 0.98 else False

    return jsonify({
        "text": text,
        "is_harmful": is_harmful,
        "confidence": float(harmful_prob)
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)