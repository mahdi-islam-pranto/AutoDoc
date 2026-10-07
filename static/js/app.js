// AutoDoc chat frontend — talks to POST /message

(() => {
    const API_URL = "/message";
    const CHANNEL = "web";
    const STORAGE_USER = "autodoc_user_id";
    const STORAGE_HISTORY = "autodoc_history";

    const $ = (id) => document.getElementById(id);
    const messagesEl = $("messages");
    const welcomeEl = $("welcome");
    const form = $("composer");
    const input = $("input");
    const sendBtn = $("sendBtn");
    const statusEl = $("statusText").parentElement;
    const statusText = $("statusText");
    const sidebar = $("sidebar");
    const scrim = $("scrim");

    const BOT_ICON =
        '<svg viewBox="0 0 24 24"><path d="M9.5 3h5v6.5H21v5h-6.5V21h-5v-6.5H3v-5h6.5z"/></svg>';

    let busy = false;

    // ───────── Storage helpers (storage may be unavailable) ─────────

    const store = {
        get(key) {
            try { return localStorage.getItem(key); } catch { return null; }
        },
        set(key, value) {
            try { localStorage.setItem(key, value); } catch { /* ignore */ }
        },
        remove(key) {
            try { localStorage.removeItem(key); } catch { /* ignore */ }
        },
    };

    function newUserId() {
        const rand = (crypto.randomUUID && crypto.randomUUID()) ||
            Math.random().toString(36).slice(2) + Date.now().toString(36);
        return `web-${rand}`;
    }

    // The backend keys conversation memory on `${channel}:${user_id}`,
    // so a new user_id means a fresh conversation thread.
    let userId = store.get(STORAGE_USER);
    if (!userId) {
        userId = newUserId();
        store.set(STORAGE_USER, userId);
    }

    let history = [];
    try { history = JSON.parse(store.get(STORAGE_HISTORY)) || []; } catch { history = []; }

    // ───────── Rendering ─────────

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    // Minimal, safe markdown: paragraphs, bullet/numbered lists, **bold**, *italic*, `code`.
    function renderMarkdown(text) {
        const inline = (s) =>
            escapeHtml(s)
                .replace(/`([^`]+)`/g, "<code>$1</code>")
                .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
                .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");

        const lines = text.replace(/\r\n/g, "\n").split("\n");
        let html = "";
        let listType = null;
        let para = [];

        const flushPara = () => {
            if (para.length) {
                html += `<p>${para.map(inline).join("<br>")}</p>`;
                para = [];
            }
        };
        const closeList = () => {
            if (listType) {
                html += `</${listType}>`;
                listType = null;
            }
        };

        for (const raw of lines) {
            const line = raw.trim();
            const bullet = line.match(/^[-*•]\s+(.*)$/);
            const numbered = line.match(/^\d+[.)]\s+(.*)$/);

            if (bullet || numbered) {
                flushPara();
                const type = bullet ? "ul" : "ol";
                if (listType !== type) {
                    closeList();
                    html += `<${type}>`;
                    listType = type;
                }
                html += `<li>${inline((bullet || numbered)[1])}</li>`;
            } else if (!line) {
                flushPara();
                closeList();
            } else {
                closeList();
                para.push(line.replace(/^#{1,6}\s+/, ""));
            }
        }
        flushPara();
        closeList();
        return html;
    }

    function formatTime(ts) {
        return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addMessage(role, text, ts = Date.now()) {
        welcomeEl.hidden = true;

        const row = document.createElement("div");
        row.className = `msg ${role === "user" ? "user" : "bot"}${role === "error" ? " error" : ""}`;

        if (role !== "user") {
            const avatar = document.createElement("div");
            avatar.className = "avatar avatar-bot";
            avatar.innerHTML = BOT_ICON;
            row.appendChild(avatar);
        }

        const body = document.createElement("div");
        body.className = "msg-body";

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        if (role === "user") bubble.textContent = text;
        else bubble.innerHTML = renderMarkdown(text);

        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = formatTime(ts);

        body.append(bubble, meta);
        row.appendChild(body);
        messagesEl.appendChild(row);
        scrollToBottom();
    }

    function showTyping() {
        const row = document.createElement("div");
        row.className = "msg bot";
        row.id = "typing";
        row.innerHTML = `
            <div class="avatar avatar-bot">${BOT_ICON}</div>
            <div class="msg-body">
                <div class="bubble typing" aria-label="AutoDoc is typing"><span></span><span></span><span></span></div>
            </div>`;
        messagesEl.appendChild(row);
        scrollToBottom();
    }

    function hideTyping() {
        const el = $("typing");
        if (el) el.remove();
    }

    function setBusy(state) {
        busy = state;
        statusEl.classList.toggle("busy", state);
        statusText.textContent = state ? "Typing…" : "Online";
        updateSendState();
    }

    function updateSendState() {
        sendBtn.disabled = busy || !input.value.trim();
    }

    function autoResize() {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 160) + "px";
    }

    function saveHistory() {
        store.set(STORAGE_HISTORY, JSON.stringify(history.slice(-100)));
    }

    // ───────── API ─────────

    // `response` is a serialized LangChain AIMessage; its content may be a
    // string or a list of content parts.
    function extractReply(data) {
        const res = data && data.response;
        if (res == null) return "";
        if (typeof res === "string") return res;

        const content = res.content ?? res;
        if (typeof content === "string") return content;
        if (Array.isArray(content)) {
            return content
                .map((part) => (typeof part === "string" ? part : part.text || ""))
                .join("");
        }
        return JSON.stringify(content);
    }

    async function sendMessage(text) {
        text = text.trim();
        if (!text || busy) return;

        const ts = Date.now();
        addMessage("user", text, ts);
        history.push({ role: "user", text, ts });
        saveHistory();

        input.value = "";
        autoResize();
        setBusy(true);
        showTyping();

        try {
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, user_id: userId, channel: CHANNEL }),
            });

            if (!res.ok) {
                let detail = `Server responded with ${res.status}`;
                try {
                    const err = await res.json();
                    if (err.detail) detail = typeof err.detail === "string" ? err.detail : detail;
                } catch { /* non-JSON error body */ }
                throw new Error(detail);
            }

            const data = await res.json();
            const reply = extractReply(data) || "Sorry, I didn't catch that. Could you rephrase?";

            hideTyping();
            const replyTs = Date.now();
            addMessage("bot", reply, replyTs);
            history.push({ role: "bot", text: reply, ts: replyTs });
            saveHistory();
        } catch (err) {
            hideTyping();
            console.error(err);
            addMessage("error", "Something went wrong while reaching AutoDoc. Please try again in a moment.");
        } finally {
            setBusy(false);
            input.focus();
        }
    }

    function resetConversation() {
        if (busy) return;
        userId = newUserId();
        store.set(STORAGE_USER, userId);
        history = [];
        store.remove(STORAGE_HISTORY);

        messagesEl.querySelectorAll(".msg").forEach((el) => el.remove());
        welcomeEl.hidden = false;
        closeSidebar();
        input.focus();
    }

    // ───────── Sidebar (mobile) ─────────

    function openSidebar() {
        sidebar.classList.add("open");
        scrim.classList.add("show");
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        scrim.classList.remove("show");
    }

    // ───────── Events ─────────

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage(input.value);
    });

    input.addEventListener("input", () => {
        autoResize();
        updateSendState();
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            sendMessage(input.value);
        }
    });

    document.querySelectorAll("[data-prompt]").forEach((btn) => {
        btn.addEventListener("click", () => {
            closeSidebar();
            sendMessage(btn.dataset.prompt);
        });
    });

    $("newChatBtn").addEventListener("click", resetConversation);
    $("resetBtn").addEventListener("click", resetConversation);
    $("menuBtn").addEventListener("click", openSidebar);
    scrim.addEventListener("click", closeSidebar);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeSidebar();
    });

    // ───────── Init ─────────

    history.forEach((m) => addMessage(m.role, m.text, m.ts));
    updateSendState();
    input.focus();
})();
