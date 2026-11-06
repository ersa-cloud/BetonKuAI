/**
 * BetonKu AI Assistant — Main Frontend Application
 *
 * Handles:
 *  - Chat send/receive with the FastAPI backend
 *  - Session management (persisted in localStorage)
 *  - Markdown rendering for AI responses
 *  - Typing indicator, quick actions, quick reply chips
 *  - Reset/confirm modal and toast notifications
 */

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════

const API_BASE = '';          // Same origin (backend serves frontend)
const CHAT_ENDPOINT = `${API_BASE}/api/chat`;
const RESET_ENDPOINT = `${API_BASE}/api/chat/reset`;
const HEALTH_ENDPOINT = `${API_BASE}/api/health`;
const SESSION_KEY = 'betonku_session_id';
const MAX_CHARS = 2000;

// ═══════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════

let sessionId = localStorage.getItem(SESSION_KEY) || '';
let isLoading = false;

// ═══════════════════════════════════════════════════════════════
// DOM REFERENCES
// ═══════════════════════════════════════════════════════════════

const chatMessages   = document.getElementById('chat-messages');
const chatInput      = document.getElementById('chat-input');
const btnSend        = document.getElementById('btn-send');
const btnReset       = document.getElementById('btn-reset');
const typingIndicator = document.getElementById('typing-indicator');
const toolIndicator  = document.getElementById('tool-indicator');
const charCounter    = document.getElementById('char-counter');
const quickActionsEl = document.getElementById('quick-actions');
const quickChipsEl   = document.getElementById('quick-chips');
const toastEl        = document.getElementById('toast');
const toastMsg       = document.getElementById('toast-message');
const toastIcon      = document.getElementById('toast-icon');
const modalReset     = document.getElementById('modal-reset');
const btnCancelReset = document.getElementById('btn-cancel-reset');
const btnConfirmReset= document.getElementById('btn-confirm-reset');

// ═══════════════════════════════════════════════════════════════
// QUICK ACTIONS CONFIGURATION
// ═══════════════════════════════════════════════════════════════

const QUICK_ACTIONS = [
  { label: '🏗️  Lihat Semua Produk & Harga',   message: 'Tampilkan daftar lengkap semua produk beton BetonKu beserta harganya' },
  { label: '🔢  Hitung Kebutuhan Beton',         message: 'Saya ingin menghitung kebutuhan volume beton untuk proyek saya' },
  { label: '📦  Cara Memesan Beton',             message: 'Bagaimana cara memesan beton di BetonKu? Apa saja syaratnya?' },
  { label: '🚚  Info Pengiriman & Radius',       message: 'Jelaskan informasi pengiriman, radius layanan, dan biaya tambahan BetonKu' },
  { label: '💳  Syarat & Metode Pembayaran',     message: 'Apa saja metode pembayaran yang diterima BetonKu dan apa syaratnya?' },
  { label: '📋  Cek Status Pesanan',             message: 'Saya ingin mengecek status pesanan saya' },
  { label: '📝  Ajukan Keluhan',                 message: 'Saya ingin mengajukan keluhan terkait pesanan saya' },
  { label: '👤  Hubungi Admin / Sales',          message: 'Saya ingin berbicara langsung dengan admin atau tim sales BetonKu' },
];

// Chips yang muncul setelah balasan AI (konteks percakapan)
const CONTEXT_CHIPS = {
  product: ['Harga K-300?', 'Beton untuk gedung 5 lantai?', 'Apa itu SCC?', 'Produk tersedia apa saja?'],
  order:   ['Buat Pesanan Sekarang', 'Cek Status Pesanan', 'Info Down Payment', 'Syarat Pengiriman'],
  calc:    ['Hitung Kolom Beton', 'Hitung Plat Lantai', 'Hitung Pondasi', 'Hitung Jalan Beton'],
  complaint: ['Keluhan Kualitas Beton', 'Keluhan Keterlambatan', 'Hubungi Admin'],
};

// ═══════════════════════════════════════════════════════════════
// MARKDOWN RENDERER (Lightweight, no external deps)
// ═══════════════════════════════════════════════════════════════

/**
 * Converts a subset of Markdown to HTML.
 * Supports: **bold**, *italic*, `code`, headers, lists, tables, blockquotes, hr.
 */
function renderMarkdown(text) {
  if (!text) return '';

  let html = text
    // Escape HTML entities first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Headers (## and ###)
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontal rule
  html = html.replace(/^---+$/gm, '<hr>');

  // Blockquote
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // Bold (**text** or __text__)
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Italic (*text* or _text_) — careful not to match bold
  html = html.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
  html = html.replace(/_([^_\n]+?)_/g, '<em>$1</em>');

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Ordered list items
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>(\n|$))+/g, (match) => `<ol>${match}</ol>`);

  // Unordered list items (-, *, •)
  html = html.replace(/^[-*•] (.+)$/gm, '<li>$1</li>');
  // Wrap consecutive <li> in <ul> (that aren't already in <ol>)
  html = html.replace(/(?<!<ol>)(<li>.*<\/li>(\n|$))+/g, (match) => `<ul>${match}</ul>`);

  // Simple table (| col | col |)
  html = html.replace(/\|(.+)\|/g, (match, content) => {
    const cells = content.split('|').map(c => c.trim());
    // Detect header separator (---|---)
    if (cells.every(c => /^[-:]+$/.test(c))) return '';
    const tag = match.includes('---') ? 'th' : 'td';
    return `<tr>${cells.map(c => `<${tag}>${c}</${tag}>`).join('')}</tr>`;
  });
  // Wrap rows in table
  html = html.replace(/(<tr>.*<\/tr>\n?)+/g, match => `<table>${match}</table>`);

  // Line breaks: double newline → paragraph break, single → <br>
  const paragraphs = html.split(/\n\n+/);
  html = paragraphs
    .map(para => {
      para = para.trim();
      if (!para) return '';
      // Don't wrap block-level elements in <p>
      if (/^<(h[1-6]|ul|ol|table|blockquote|hr|pre)/.test(para)) return para;
      // Single newline inside a paragraph → <br>
      return `<p>${para.replace(/\n/g, '<br>')}</p>`;
    })
    .join('\n');

  return html;
}

// ═══════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

let toastTimer = null;

function showToast(message, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };
  toastMsg.textContent = message;
  toastIcon.textContent = icons[type] || 'ℹ️';
  toastEl.classList.remove('hidden');
  toastEl.classList.add('toast-show');
  toastEl.classList.remove('toast-hide');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.add('toast-hide');
    setTimeout(() => toastEl.classList.add('hidden'), 300);
  }, 3500);
}

// ═══════════════════════════════════════════════════════════════
// CHAT RENDERING
// ═══════════════════════════════════════════════════════════════

/**
 * Format a timestamp to a short human-readable string.
 */
function formatTime(date = new Date()) {
  return date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Appends a user message bubble to the chat.
 */
function appendUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'flex items-end justify-end gap-3 message-enter';
  div.innerHTML = `
    <div class="flex flex-col gap-1 items-end max-w-[80%]">
      <div class="bg-navy text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-chat text-sm leading-relaxed">
        ${escapeHtml(text)}
      </div>
      <span class="text-xs text-gray-400 pr-1">Anda · ${formatTime()}</span>
    </div>
    <div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0 mb-5">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
    </div>
  `;
  chatMessages.appendChild(div);
  scrollToBottom();
}

/**
 * Appends an AI message bubble to the chat.
 * Content is rendered as Markdown.
 */
function appendAIMessage(text, toolCallsMade = []) {
  const div = document.createElement('div');
  div.className = 'flex items-start gap-3 ai-message message-enter';

  // Build optional tool-calls badge
  let toolBadge = '';
  if (toolCallsMade && toolCallsMade.length > 0) {
    const toolNames = toolCallsMade.map(formatToolName).join(', ');
    toolBadge = `
      <div class="flex items-center gap-1.5 mt-2 text-xs text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
        <span>Data: ${toolNames}</span>
      </div>
    `;
  }

  div.innerHTML = `
    <div class="w-8 h-8 bg-orange rounded-full flex items-center justify-center font-bold text-white text-sm flex-shrink-0 mt-0.5 shadow-sm">S</div>
    <div class="flex flex-col gap-1 max-w-[85%]">
      <div class="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-chat text-sm text-gray-700 leading-relaxed border border-gray-100">
        <div class="ai-content">${renderMarkdown(text)}</div>
        ${toolBadge}
      </div>
      <span class="text-xs text-gray-400 pl-1">Sari · ${formatTime()}</span>
    </div>
  `;
  chatMessages.appendChild(div);
  scrollToBottom();
}

/**
 * Convert tool function name to human-friendly label.
 */
function formatToolName(name) {
  const labels = {
    get_product_catalog:      'Katalog Produk',
    get_product_detail:       'Detail Produk',
    calculate_concrete_volume:'Kalkulator Beton',
    get_company_information:  'Info Perusahaan',
    create_order_request:     'Buat Pesanan',
    check_order_status:       'Status Pesanan',
    submit_complaint:         'Catat Keluhan',
    request_admin_handoff:    'Eskalasi Admin',
  };
  return labels[name] || name;
}

/**
 * Safely escapes HTML to prevent XSS in user messages.
 */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>');
}

/**
 * Smooth scroll to the bottom of the chat container.
 */
function scrollToBottom() {
  requestAnimationFrame(() => {
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  });
}

// ═══════════════════════════════════════════════════════════════
// LOADING STATE
// ═══════════════════════════════════════════════════════════════

function setLoading(loading) {
  isLoading = loading;
  btnSend.disabled = loading || chatInput.value.trim().length === 0;
  chatInput.disabled = loading;

  if (loading) {
    typingIndicator.classList.remove('hidden');
    scrollToBottom();
  } else {
    typingIndicator.classList.add('hidden');
    toolIndicator.classList.remove('flex');
    toolIndicator.classList.add('hidden');
  }
}

function showToolIndicator() {
  toolIndicator.classList.remove('hidden');
  toolIndicator.classList.add('flex');
}

// ═══════════════════════════════════════════════════════════════
// QUICK REPLY CHIPS
// ═══════════════════════════════════════════════════════════════

/**
 * Renders contextual quick-reply chips based on message content.
 * Clears chips after a message is sent.
 */
function updateQuickChips(aiReply) {
  quickChipsEl.innerHTML = '';
  const reply = (aiReply || '').toLowerCase();

  let chips = [];

  if (reply.includes('produk') || reply.includes('harga') || reply.includes('beton k-')) {
    chips = CONTEXT_CHIPS.product;
  } else if (reply.includes('pesan') || reply.includes('order') || reply.includes('pengiriman')) {
    chips = CONTEXT_CHIPS.order;
  } else if (reply.includes('hitung') || reply.includes('volume') || reply.includes('m³') || reply.includes('kalkul')) {
    chips = CONTEXT_CHIPS.calc;
  } else if (reply.includes('keluhan') || reply.includes('komplain') || reply.includes('masalah')) {
    chips = CONTEXT_CHIPS.complaint;
  }

  chips.slice(0, 4).forEach(chipText => {
    const btn = document.createElement('button');
    btn.className = 'chip-btn';
    btn.textContent = chipText;
    btn.addEventListener('click', () => {
      sendMessage(chipText);
      quickChipsEl.innerHTML = '';
    });
    quickChipsEl.appendChild(btn);
  });
}

// ═══════════════════════════════════════════════════════════════
// QUICK ACTIONS SIDEBAR
// ═══════════════════════════════════════════════════════════════

function renderQuickActions() {
  quickActionsEl.innerHTML = '';
  QUICK_ACTIONS.forEach(action => {
    const btn = document.createElement('button');
    btn.className = 'quick-action-btn w-full text-left text-xs font-medium text-gray-600 hover:text-navy hover:bg-gray-50 border border-gray-100 hover:border-gray-200 rounded-xl px-3 py-2.5 transition-all duration-200 flex items-center gap-2';
    btn.textContent = action.label;
    btn.dataset.message = action.message;
    btn.addEventListener('click', () => {
      sendMessage(action.message);
      // On mobile, scroll to chat area
      document.querySelector('section').scrollIntoView({ behavior: 'smooth' });
    });
    quickActionsEl.appendChild(btn);
  });
}

// ═══════════════════════════════════════════════════════════════
// API COMMUNICATION
// ═══════════════════════════════════════════════════════════════

/**
 * Sends a message to the backend and handles the AI response.
 */
async function sendMessage(messageText) {
  const text = (messageText || chatInput.value).trim();
  if (!text || isLoading) return;

  // Clear input and chips
  chatInput.value = '';
  charCounter.textContent = `0/${MAX_CHARS}`;
  btnSend.disabled = true;
  quickChipsEl.innerHTML = '';
  autoResizeTextarea();

  // Render user message immediately
  appendUserMessage(text);
  setLoading(true);

  // Show tool indicator slightly after typing indicator
  setTimeout(() => {
    if (isLoading) showToolIndicator();
  }, 800);

  try {
    const response = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMsg = errorData.detail || `HTTP Error ${response.status}`;
      throw new Error(errorMsg);
    }

    const data = await response.json();

    // Update session ID (might be new if first message)
    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem(SESSION_KEY, sessionId);
    }

    // Render AI reply
    setLoading(false);
    appendAIMessage(data.reply, data.tool_calls_made);
    updateQuickChips(data.reply);

  } catch (error) {
    setLoading(false);

    const isNetworkError = error.message.includes('fetch') || error.message.includes('Failed');
    const userMessage = isNetworkError
      ? 'Tidak dapat terhubung ke server. Pastikan backend sudah berjalan.'
      : error.message;

    appendAIMessage(`❌ **Terjadi kesalahan:** ${userMessage}\n\nSilakan coba lagi atau hubungi tim kami di **+62 21 8900-1234**.`);
    showToast(userMessage, 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
// RESET CHAT
// ═══════════════════════════════════════════════════════════════

async function resetChat() {
  if (sessionId) {
    try {
      await fetch(RESET_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch {
      // Silent fail — reset local state regardless
    }
  }

  // Clear local state
  sessionId = '';
  localStorage.removeItem(SESSION_KEY);

  // Clear chat UI (keep welcome message)
  const allMessages = chatMessages.querySelectorAll('.ai-message, .flex.justify-end');
  allMessages.forEach(el => el.remove());

  // Re-add welcome message
  const welcomeMsg = document.getElementById('welcome-message');
  if (!welcomeMsg) {
    // Re-create if it was removed
    location.reload();
    return;
  }

  quickChipsEl.innerHTML = '';
  chatInput.value = '';
  autoResizeTextarea();
  showToast('Percakapan berhasil direset. Mulai obrolan baru!', 'success');
}

// ═══════════════════════════════════════════════════════════════
// INPUT HANDLING
// ═══════════════════════════════════════════════════════════════

/**
 * Auto-resize textarea to fit content (up to max-height).
 */
function autoResizeTextarea() {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 128) + 'px';
}

/**
 * Handle Enter key: send on Enter, newline on Shift+Enter.
 */
function handleInputKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isLoading && chatInput.value.trim()) {
      sendMessage();
    }
  }
}

// ═══════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════

/**
 * Check API status on startup and warn if API key isn't configured.
 */
async function checkApiHealth() {
  try {
    const res = await fetch(HEALTH_ENDPOINT);
    if (!res.ok) return;
    const data = await res.json();

    if (!data.api_key_configured) {
      showToast('API Key belum dikonfigurasi. Silakan isi OPENAI_API_KEY di file .env', 'warning');
      // Show a persistent warning in chat
      setTimeout(() => {
        appendAIMessage(
          '⚠️ **Perhatian:** OpenAI API Key belum dikonfigurasi.\n\n' +
          'Untuk mengaktifkan AI, salin file `.env.example` menjadi `.env` dan isi `OPENAI_API_KEY` dengan API key Anda.\n\n' +
          'Setelah itu, restart server dengan `uvicorn main:app --reload`.'
        );
      }, 500);
    }
  } catch {
    // Server might not be ready yet, silent fail
  }
}

// ═══════════════════════════════════════════════════════════════
// EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════

// Input events
chatInput.addEventListener('input', () => {
  autoResizeTextarea();
  const len = chatInput.value.length;
  charCounter.textContent = `${len}/${MAX_CHARS}`;
  btnSend.disabled = isLoading || len === 0 || len > MAX_CHARS;

  // Visual feedback for character limit
  if (len > MAX_CHARS * 0.9) {
    charCounter.classList.add('text-orange-500');
  } else {
    charCounter.classList.remove('text-orange-500');
  }
});

chatInput.addEventListener('keydown', handleInputKeydown);

// Send button
btnSend.addEventListener('click', () => sendMessage());

// Reset button → show modal
btnReset.addEventListener('click', () => {
  modalReset.classList.remove('hidden');
  modalReset.classList.add('flex');
});

// Modal cancel
btnCancelReset.addEventListener('click', () => {
  modalReset.classList.add('hidden');
  modalReset.classList.remove('flex');
});

// Modal confirm reset
btnConfirmReset.addEventListener('click', async () => {
  modalReset.classList.add('hidden');
  modalReset.classList.remove('flex');
  await resetChat();
});

// Close modal on backdrop click
modalReset.addEventListener('click', (e) => {
  if (e.target === modalReset) {
    modalReset.classList.add('hidden');
    modalReset.classList.remove('flex');
  }
});

// Quick action buttons in sidebar (using event delegation)
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.quick-action-btn');
  if (btn && btn.dataset.message) {
    sendMessage(btn.dataset.message);
  }
});

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

(function init() {
  renderQuickActions();
  autoResizeTextarea();
  checkApiHealth();

  // Focus input on desktop
  if (window.innerWidth >= 1024) {
    chatInput.focus();
  }

  // If we have a stored session ID, show a subtle indicator
  if (sessionId) {
    console.info(`[BetonKu] Melanjutkan sesi: ${sessionId}`);
  }
})();
