const bottle = document.getElementById('bottle');
const messageSection = document.getElementById('message-section');

/* ---------------- API ---------------- */
const api = {
    // Vercel routes are unified under /api
    get: (url) =>
        fetch(`/api${url}`).then(res => res.json()),

    post: async (url, body = {}) => {
        const res = await fetch(`/api${url}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        // If the backend returns 403, it means the AI safety check failed
        if (res.status === 403) {
            alert("This message is too toxic to throw into the sea!");
            throw new Error("Toxic content blocked");
        }
        
        return res.json();
    }
};

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
        console.error("Connection error:", err);
    }
});

/* ---------------- RENDERS ---------------- */
function renderOptions(message) {
    ui.showTemplate("options-template");
    messageSection.querySelector(".message-text").textContent = `Message: ${message.text}`;

    messageSection.querySelector(".btn-resend").onclick = () => handleResend(message.id);
    messageSection.querySelector(".btn-reply").onclick = () => renderReplyForm(message);
    messageSection.querySelector(".btn-new").onclick = renderWriteForm;
}

function renderWriteForm() {
    ui.showTemplate("write-template");

    document.getElementById('btn-submit').onclick = async () => {
        const text = document.getElementById('letter').innerText.trim(); 
        
        if (!text) {
            alert("The bottle is empty!");
            return;
        }

        try {
            // The safety check now happens inside this POST call on the backend
            await api.post('/submit', { message: text });
            
            ui.animateBottle();
            ui.clear();
        } catch (err) {
            // Safety check failure or server error handled here
            console.warn("Submit failed:", err.message);
        }
    };
}

function renderReplyForm(message) {
    ui.showTemplate("reply-template");
    messageSection.querySelector(".replying-to").textContent = `Replying to: ${message.text}`;

    document.getElementById('btn-submit-reply').onclick = async () => {
        const reply = document.getElementById('reply-text').innerText.trim();
        if (!reply) return;

        try {
            // Safety check happens on the server
            await api.post(`/reply/${message.id}`, { replyText: reply });
            
            ui.animateBottle();
            ui.clear();
        } catch (err) {
            console.warn("Reply failed:", err.message);
        }
    };
}

function handleResend(id) {
    ui.animateBottle();
    ui.clear();
    api.post(`/resend/${id}`).catch(() => console.warn("Resend failed"));
}