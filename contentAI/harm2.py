import joblib
import sys
import sklearn.linear_model

# Keep the fix for older sklearn versions
sys.modules['sklearn.linear_model.logistic'] = sklearn.linear_model._logistic

# 1. Load both "brains"
vectorizer = joblib.load('tfidf_vectorizer.pkl')
model = joblib.load('hate_speech_model.pkl')

def test_letter(text):
    # 2. Vectorize the raw text first
    # We put [text] in a list because the vectorizer expects an iterable
    text_tfidf = vectorizer.transform([text])
    
    # 3. Use the transformed data to predict
    prediction = model.predict(text_tfidf)[0]
    confidence = model.predict_proba(text_tfidf)
    
    status = "🚩 HARMFUL" if prediction == 1 else "✅ SAFE"
    
    # If prediction is 1 (Harmful), show the probability of class 1
    # If prediction is 0 (Safe), show the probability of class 0
    prob = confidence[0][1] if prediction == 1 else confidence[0][0]
    
    print(f"Letter: '{text}'")
    print(f"Result: {status} ({prob*100:.2f}% confident)\n")

# Test scenarios
test_letter("I love the backwaters in Kochi, so peaceful.")
test_letter("I am going to hurt you if I find you bitch.")
test_letter("This traffic is absolute trash, I hate everyone here.")
test_letter("I love killing and torturing people.")
test_letter("i hate feeling so sad")
test_letter("")