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

# 1. Get URI from environment
uri = os.environ.get("MONGO_URI")

# 2. Extract database name from URI (Mongoose does this automatically, PyMongo needs help)
# If your URI is mongodb+srv://.../dbname?..., this gets 'dbname'
db_name = uri.split('/')[-1].split('?')[0] 

app.config["MONGO_URI"] = uri
# Explicitly tell Flask-PyMongo which database to use
mongo = PyMongo(app, uri=uri)

def get_db():
    # If the connection is failing, this will now tell us WHY in the logs
    if mongo.db is None:
        print(f"DEBUG: MONGO_URI starts with: {uri[:15]}...")
        print(f"DEBUG: Detected DB Name: {db_name}")
        raise RuntimeError("Database connection not established. Check MONGO_URI and Network Access.")
    return mongo.db[db_name].messages # Use the explicit database name


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
        return harmful_prob < 0.98
    except Exception as e:
        print(f"AI Error: {e}")
        return True 

# --- Routes ---

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
    result = get_db().insert_one(new_doc)
    return jsonify({"status": "accepted", "id": str(result.inserted_id)})

@app.route('/api/random', methods=['GET'])
def get_random():
    if random.random() > 0.6:
        return jsonify({"hasMessage": False})

    selected = get_db().find_one_and_update(
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

@app.route('/api/reply/<id>', methods=['POST'])
def reply(id):
    data = request.get_json()
    reply_text = data.get('replyText', '')

    if not is_safe(reply_text):
        return jsonify({"success": False, "error": "Inappropriate reply"}), 403

    message = get_db().find_one({"_id": ObjectId(id)})
    if not message:
        return jsonify({"error": "Bottle lost at sea"}), 404

    updated_text = f"{message['text']}\n\nReply: {reply_text}"
    
    get_db().update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "text": updated_text,
            "locked": False,
            "lockedAt": None
        }}
    )

    return jsonify({"success": True, "status": "reply added"})

@app.route('/api/resend/<id>', methods=['POST'])
def resend(id):
    get_db().update_one(
        {"_id": ObjectId(id)},
        {"$set": {"locked": False, "lockedAt": None}}
    )
    return jsonify({"success": True})