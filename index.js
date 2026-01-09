const bottle = document.getElementById('bottle');
const messageSection = document.getElementById('message-section');

/* ---------------- API ---------------- */
const api = {
    // We remove "http://localhost:3000" and just use the URL
    // Vercel will automatically point this to your current domain
    get: (url) =>
        fetch(`/api${url}`).then(res => res.json()),

    post: (url, body = {}) =>
        fetch(`/api${url}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(res => res.json())
};
/* ---------------- AI SAFETY CHECK ---------------- */
async function isSafe(text) {
    try {
        // This points to your Python Flask server
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const result = await response.json();
        
        // If the model says it is NOT harmful, return true (it is safe)
        // This uses the 98% logic we set up in the Flask app
        return result.is_harmful === false; 
        
    } catch (err) {
        console.error("AI Service Down:", err);
        // Fallback: If your Python server isn't running, we let it pass
        return true; 
    }
}

/* ---------------- UI ---------------- */
const ui = {
    clear() {
        messageSection.innerHTML = '';
        messageSection.classList.remove("message");
        messageSection.style.display = 'none';
    },

    showTemplate(id) {
        messageSection.innerHTML = '';
        const tpl = document.getElementById(id).content.cloneNode(true);
        messageSection.appendChild(tpl);
        messageSection.style.display = 'block';
        messageSection.classList.add("message");
    },

    animateBottle() {
        bottle.classList.add("sailing");
        setTimeout(() => bottle.classList.remove("sailing"), 3000);
    }
};

/* ---------------- CORE ---------------- */
bottle.addEventListener('click', async () => {
    try {
        const data = await api.get('/random');

        if (!data.hasMessage) {
            renderWriteForm();
        } else {
            renderOptions(data.message);
        }
    } catch (err) {
        console.error("Server not running?", err);
    }
});

/* ---------------- RENDERS ---------------- */
function renderOptions(message) {
    ui.showTemplate("options-template");

    messageSection.querySelector(".message-text").textContent =
        `Message: ${message.text}`;

    messageSection.querySelector(".btn-resend").onclick =
        () => handleResend(message.id);

    messageSection.querySelector(".btn-reply").onclick =
        () => renderReplyForm(message);

    messageSection.querySelector(".btn-new").onclick =
        renderWriteForm;
}

/* ---------------- RENDERS ---------------- */
function renderWriteForm() {
    ui.showTemplate("write-template");

    document.getElementById('btn-submit').onclick = async () => { // Added async
        // FIX: Use innerText because it is a contenteditable DIV, not an input/textarea
        const text = document.getElementById('letter').innerText.trim(); 
        
        if (!text) {
            alert("The bottle is empty! Write something first.");
            return;
        }

        // --- ADD THE AI SAFETY CHECK HERE ---
        const safe = await isSafe(text); // Using the function we built earlier
        if (!safe) {
            alert("This message is too toxic to throw into the sea! (98%+ confidence)");
            return; 
        }

        ui.animateBottle();
        ui.clear();

        api.post('/submit', { message: text })
            .then(res => console.log("Submit:", res))
            .catch(() => console.warn("Submit failed silently"));
    };
}

function renderReplyForm(message) {
    ui.showTemplate("reply-template");

    messageSection.querySelector(".replying-to").textContent =
        `Replying to: ${message.text}`;

    // 1. Added 'async' here so we can use 'await' inside
    document.getElementById('btn-submit-reply').onclick = async () => {
        
        // 2. Changed .value to .innerText (matches your contenteditable div style)
        const reply = document.getElementById('reply-text').innerText.trim();
        
        if (!reply) return;

        // 3. AI Safety Check
        const safe = await isSafe(reply);
        if (!safe) {
            alert("Your reply is too toxic for the ocean! (98%+ confidence)");
            return; // Stops the bottle from sailing
        }

        ui.animateBottle();
        ui.clear();

        api.post(`/reply/${message.id}`, { replyText: reply })
            .then(res => console.log("Reply:", res))
            .catch(() => console.warn("Reply failed silently"));
    };
}

/* ---------------- ACTIONS ---------------- */
function handleResend(id) {
    ui.animateBottle();
    ui.clear();

    api.post(`/resend/${id}`)
        .then(res => console.log("Resent:", res))
        .catch(() => console.warn("Resend failed silently"));
}
