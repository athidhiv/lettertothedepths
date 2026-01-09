from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os

app = Flask(__name__)
CORS(app)

# Use absolute paths to locate models inside the Vercel /api folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
vectorizer = joblib.load(os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl'))
model = joblib.load(os.path.join(BASE_DIR, 'hate_speech_model.pkl'))

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"is_harmful": False, "confidence": 0})

    vector = vectorizer.transform([text])
    probabilities = model.predict_proba(vector)[0]
    harmful_prob = probabilities[1] 

    is_harmful = True if harmful_prob >= 0.98 else False

    return jsonify({
        "is_harmful": is_harmful,
        "confidence": float(harmful_prob)
    })

# NO app.run() here for Vercel!