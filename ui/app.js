const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatWindow = document.getElementById('chat-window');
const welcomeState = document.getElementById('welcome-state');
const sendBtn = document.getElementById('send-btn');
const staleBanner = document.getElementById('stale-banner');
const staleDateSpan = document.getElementById('stale-date');

function submitPrompt(query) {
    chatInput.value = query;
    chatForm.dispatchEvent(new Event('submit'));
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    // Hide welcome state
    if (welcomeState) {
        welcomeState.style.display = 'none';
    }

    // Append User Message
    appendMessage(query, 'user');
    chatInput.value = '';
    
    // Disable input and show loading
    chatInput.disabled = true;
    sendBtn.disabled = true;
    const loadingId = appendLoading();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();
        
        // Remove Loading
        document.getElementById(loadingId)?.remove();

        // Handle Response
        if (data.type === 'factual') {
            appendFactual(data);
        } else if (data.type === 'refusal') {
            appendRefusal(data);
        } else if (data.detail) {
            appendError(data.detail[0]?.msg || 'API Error');
        } else {
            appendError('An unknown error occurred.');
        }

        // Handle Stale Banner
        if (data.is_stale && data.last_updated) {
            staleDateSpan.textContent = data.last_updated;
            staleBanner.classList.add('visible');
        } else {
            staleBanner.classList.remove('visible');
        }

    } catch (err) {
        document.getElementById(loadingId)?.remove();
        appendError('Failed to connect to the server. Please ensure the backend is running.');
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
        scrollToBottom();
    }
});

function appendMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    
    const icon = sender === 'user' ? 'person' : 'smart_toy';
    
    msgDiv.innerHTML = `
        <div class="avatar ${sender}">
            <span class="material-symbols-outlined">${icon}</span>
        </div>
        <div class="message-content">
            <p>${text}</p>
        </div>
    `;
    chatWindow.appendChild(msgDiv);
    scrollToBottom();
}

function appendLoading() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = id;
    msgDiv.className = `message bot`;
    msgDiv.innerHTML = `
        <div class="avatar bot">
            <span class="material-symbols-outlined">smart_toy</span>
        </div>
        <div class="message-content">
            <div class="typing-wave">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatWindow.appendChild(msgDiv);
    scrollToBottom();
    return id;
}

function appendFactual(data) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message bot`;
    
    msgDiv.innerHTML = `
        <div class="avatar bot">
            <span class="material-symbols-outlined">smart_toy</span>
        </div>
        <div class="message-content factual-response">
            <p>${data.answer}</p>
            ${data.source ? `
                <a href="${data.source}" target="_blank" class="source-link">
                    <span class="material-symbols-outlined">link</span>
                    Source (Groww)
                </a>
            ` : ''}
            ${data.last_updated ? `<div class="date-footer">Last updated from sources: ${data.last_updated}</div>` : ''}
        </div>
    `;
    chatWindow.appendChild(msgDiv);
}

function appendRefusal(data) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message bot`;
    
    let linksHtml = '';
    if (data.corpus_links && data.corpus_links.length > 0) {
        linksHtml = '<div class="fund-links">' + 
            data.corpus_links.map(url => {
                const nameMatch = url.match(/mutual-funds\/(.+)$/);
                const name = nameMatch ? nameMatch[1].split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : 'Groww Fund Page';
                return `<a href="${url}" target="_blank" class="fund-link-item">${name}</a>`;
            }).join('') + 
        '</div>';
    }

    msgDiv.innerHTML = `
        <div class="avatar bot" style="background: var(--warning-border)">
            <span class="material-symbols-outlined">warning</span>
        </div>
        <div class="message-content refusal-response">
            <div class="message-text">${data.answer}</div>
            ${linksHtml}
            ${data.last_updated ? `<div class="date-footer">Last updated from sources: ${data.last_updated}</div>` : ''}
        </div>
    `;
    chatWindow.appendChild(msgDiv);
}

function appendError(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message bot`;
    msgDiv.innerHTML = `
        <div class="avatar bot" style="background: #ef4444">
            <span class="material-symbols-outlined">error</span>
        </div>
        <div class="message-content" style="border-color: #ef4444; color: #fca5a5;">
            <p>${text}</p>
        </div>
    `;
    chatWindow.appendChild(msgDiv);
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}
