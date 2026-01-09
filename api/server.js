const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const badWords = require('../assets/bad_words.json'); 
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// --- Database Connection ---
mongoose.connect(process.env.MONGO_URI);
const Message = mongoose.model('Message', new mongoose.Schema({
  text: { type: String, required: true },
  locked: { type: Boolean, default: false },
  lockedAt: { type: Date, default: null },
  createdAt: { type: Date, default: Date.now }
}));

// --- Middleware/Helper: Moderation ---
// Fixed: Now handles cases where badWords might not be passed correctly
// Replace your old isSafe function with this:
async function isSafe(text) {
  try {
    const response = await fetch('http://localhost:5000/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    
    const result = await response.json();
    
    // If the model says it is NOT harmful, return true (it is safe)
    return result.is_harmful === false; 
    
  } catch (err) {
    console.error("AI Service Down:", err);
    return true; // Fallback: Allow if AI is offline, or set to false to be strict
  }
}

// --- Routes ---

// 1. Submit New Bottle
app.post('/submit', async (req, res) => {
  const { message } = req.body;
  if (!(await isSafe(message))) {
    return res.status(403).json({ success: false, error: 'Inappropriate content' });
  }

  try {
    const saved = await Message.create({ text: message });
    res.json({ status: 'accepted', id: saved._id });
  } catch (err) {
    res.status(500).json({ error: 'Database error' });
  }
});

// 2. Get Random Bottle (and Lock it)
app.get('/random', async (req, res) => {
  if (Math.random() > 0.6) return res.json({ hasMessage: false });

  try {
    const selected = await Message.findOneAndUpdate(
      { locked: false },
      { $set: { locked: true, lockedAt: new Date() } },
      { new: true }
    );

    if (!selected) return res.json({ hasMessage: false });
    res.json({ hasMessage: true, message: { id: selected._id, text: selected.text } });
  } catch (err) {
    res.status(500).json({ error: 'Fetch error' });
  }
});

// 3. Reply to Bottle
app.post('/reply/:id', async (req, res) => {
  const { replyText } = req.body;
  if (!(await isSafe(replyText))) {
    return res.status(403).json({ success: false, error: 'Inappropriate reply' });
  }

  try {
    const message = await Message.findById(req.params.id);
    if (!message) return res.status(404).json({ error: 'Bottle lost at sea' });

    message.text += `\n\nReply: ${replyText}`;
    message.locked = false;
    message.lockedAt = null;
    await message.save();

    res.json({ success: true, status: 'reply added' });
  } catch (err) {
    res.status(500).json({ error: 'Reply failed' });
  }
});

// 4. Unlock/Resend
app.post('/resend/:id', async (req, res) => {
  try {
    await Message.findByIdAndUpdate(req.params.id, { locked: false, lockedAt: null });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Unlock failed' });
  }
});

// --- Cleanup Task (Every Hour) ---
setInterval(async () => {
  const oneHourAgo = new Date(Date.now() - (60 * 60 * 1000));
  await Message.deleteMany({ locked: true, lockedAt: { $lt: oneHourAgo } });
}, 3600000);

module.exports = app;