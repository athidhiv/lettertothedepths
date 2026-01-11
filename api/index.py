from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import joblib
import os
import datetime
import random

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# Set your MONGO_URI in Vercel Environment Variables
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)
db = mongo.db.messages # Access the 'messages' collection

# --- Load ML Models ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
vectorizer = joblib.load(os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl'))
model = joblib.load(os.path.join(BASE_DIR, 'hate_speech_model.pkl'))

# --- Helper: AI Moderation ---
def is_safe(text):
    if not text:
        return True
    try:
        vector = vectorizer.transform([text])
        probabilities = model.predict_proba(vector)[0]
        harmful_prob = probabilities[1] 
        # Returns True if NOT harmful
        return harmful_prob < 0.98
    except Exception as e:
        print(f"AI Error: {e}")
        return True # Fallback: Allow if model fails

# --- Routes ---

# 1. Submit New Bottle
@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.get_json()
    message_text = data.get('message', '')

    if not is_safe(message_text):
        return jsonify({"success": False, "error": "Inappropriate content"}), 403

    new_doc = {
        "text": message_text,
        "locked": False,
        "lockedAt": None,
        "createdAt": datetime.datetime.utcnow()
    }
    result = db.insert_one(new_doc)
    return jsonify({"status": "accepted", "id": str(result.inserted_id)})

# 2. Get Random Bottle (and Lock it)
@app.route('/api/random', methods=['GET'])
def get_random():
    # Keep the 40% "nothing found" logic from your Node backend
    if random.random() > 0.6:
        return jsonify({"hasMessage": False})

    # Find one unlocked message and lock it
    selected = db.find_one_and_update(
        {"locked": False},
        {"$set": {"locked": True, "lockedAt": datetime.datetime.utcnow()}},
        new=True
    )

    if not selected:
        return jsonify({"hasMessage": False})

    return jsonify({
        "hasMessage": True, 
        "message": {
            "id": str(selected["_id"]), 
            "text": selected["text"]
        }
    })

# 3. Reply to Bottle
@app.route('/api/reply/<id>', methods=['POST'])
def reply(id):
    data = request.get_json()
    reply_text = data.get('replyText', '')

    if not is_safe(reply_text):
        return jsonify({"success": False, "error": "Inappropriate reply"}), 403

    message = db.find_one({"_id": ObjectId(id)})
    if not message:
        return jsonify({"error": "Bottle lost at sea"}), 404

    updated_text = f"{message['text']}\n\nReply: {reply_text}"
    
    db.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "text": updated_text,
            "locked": False,
            "lockedAt": None
        }}
    )

    return jsonify({"success": True, "status": "reply added"})

# 4. Unlock/Resend
@app.route('/api/resend/<id>', methods=['POST'])
def resend(id):
    db.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"locked": False, "lockedAt": None}}
    )
    return jsonify({"success": True})

# Note: Vercel does not support long-running setInterval. 
# For the cleanup task, use Vercel Cron Jobs (vercel.json).