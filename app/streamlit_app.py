"""
ShopAssist — Accord Business Group
Product Discovery Chatbot
"""

import streamlit as st
import plotly.graph_objects as go
from rag import RAGPipeline
from chatbot import Chatbot

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopAssist — Accord Business Group",
    page_icon="🤖",
    layout="wide",
)

## Streamlit's default styles
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
  #MainMenu, footer, header { visibility: hidden; }
  .stApp { background: #EEF2FB; }
  .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }

  [data-testid="stSidebar"] { background: #0F2557 !important; overflow: hidden !important; }
  [data-testid="stSidebar"] * { color: #ffffff !important; }
  [data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,0.2) !important; }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12) !important; }

  [data-testid="stSidebarContent"] {
    height: 100vh !important;
    overflow-y: auto !important;
    padding-bottom: 70px !important;
    display: flex !important;
    flex-direction: column !important;
  }

  .abg-sidebar-logo { display:flex; align-items:center; gap:10px; padding:4px 0 16px; border-bottom:1px solid rgba(255,255,255,0.12); margin-bottom:16px; }
  .abg-box { background:#2563EB; color:#ffffff !important; font-weight:700; font-size:14px; padding:6px 10px; border-radius:6px; letter-spacing:1px; }
  .abg-fullname { font-size:11px; color:rgba(255,255,255,0.65) !important; line-height:1.5; }

  .user-bubble { background:#2563EB; color:#ffffff; padding:12px 18px; border-radius:16px 16px 4px 16px; max-width:60%; margin-left:auto; font-size:14px; line-height:1.6; margin-bottom:12px; display:block; }
  .bot-bubble { background:#F8FAFF; color:#1E293B; padding:12px 18px; border-radius:16px 16px 16px 4px; max-width:65%; font-size:14px; line-height:1.6; border:1px solid #D1DCF5; border-left:3px solid #2563EB; margin-bottom:12px; display:block; }
  .cat-badge { display:inline-block; background:#EEF2FB; color:#1A3C8F; border:1px solid #B8CAF0; border-radius:20px; padding:4px 14px; font-size:12px; font-weight:500; margin-bottom:8px; }

  [data-testid="stChatInput"] { border:1px solid #B8CAF0 !important; background:#ffffff !important; border-radius:16px !important; min-height:60px !important; }
  [data-testid="stChatInput"] textarea { color:#1E293B !important; background:#ffffff !important; caret-color:#1E293B !important; font-size:15px !important; min-height:60px !important; padding:16px !important; }
  [data-testid="stChatInput"] textarea::placeholder { color:#94A3B8 !important; font-size:15px !important; }

  hr { border-color:#D1DCF5 !important; }

  /* Language button fixed at bottom of sidebar always */
  .lang-fixed {
    position: fixed;
    bottom: 16px;
    left: 16px;
    z-index: 99999;
  }
  .lang-fixed .stButton > button {
    background: #2563EB !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    padding: 6px 16px !important;
    min-height: 0 !important;
    height: 34px !important;
    letter-spacing: 0.5px !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Load chatbot once ─────────────────────────────────────────────────────────
# Without this, the RAG pipeline would reload on every user interaction
@st.cache_resource
def load_chatbot():
    """Initialize RAG pipeline and chatbot engine."""
    rag = RAGPipeline()
    rag.load()
    return Chatbot(rag)

bot = load_chatbot()

# ── Chart Functions ─────────────────────────────────────────────────────────────
def category_donut_chart(history: list):
    """Donut chart showing which categories the user browsed."""
    counts = {}
    for c in history:
        counts[c] = counts.get(c, 0) + 1
    if not counts:
        return None
    labels = list(counts.keys())
    values = list(counts.values())
    colors = ["#2563EB", "#00D4FF", "#1D9E75", "#F59E0B"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.6,
        marker=dict(colors=colors[:len(labels)], line=dict(color="#0F2557", width=2)),
        textfont=dict(color="white", size=10),
        hovertemplate="%{label}: %{value}<extra></extra>",
        showlegend=True,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0),
        height=180,
        legend=dict(font=dict(color="white", size=9), bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def catalog_bar_chart():
    """Bar chart showing product catalog distribution by category."""
    cats   = ["Wall\nChargers", "Power\nBanks", "Travel\nBags", "Home &\nKitchen"]
    counts = [10, 10, 10, 10]
    colors = ["#2563EB", "#00D4FF", "#1D9E75", "#F59E0B"]
    fig = go.Figure(go.Bar(
        x=cats, y=counts,
        marker=dict(color=colors, line=dict(color="rgba(0,0,0,0)")),
        text=counts, textposition="auto",
        textfont=dict(color="white", size=11),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0),
        height=180,
        xaxis=dict(showgrid=False, tickfont=dict(color="white", size=9)),
        yaxis=dict(showgrid=False, visible=False),
    )
    return fig

TEXT = {
    "ar": {
        "subtitle":    "أخبرني ماذا تحتاج وسأساعدك في العثور على المنتج المناسب",
        "new_chat":    "➕ محادثة جديدة",
        "prev_chats":  "المحادثات السابقة",
        "no_chats":    "لا توجد محادثات سابقة",
        "welcome":     "اكتب رسالتك أدناه للبدء",
        "placeholder": "اكتب رسالتك هنا...",
        "thinking":    "جاري التفكير...",
        "category":    "الفئة",
        "categories": {
            "wall_chargers": "🔌 شواحن حائط",
            "power_banks":   "🔋 بطاريات محمولة",
            "travel_bags":   "🎒 حقائب سفر",
            "home_kitchen":  "🏠 منزل ومطبخ",
        },
    },
    "en": {
        "subtitle":    "Tell me what you need and I'll find the perfect product for you",
        "new_chat":    "➕ New Chat",
        "prev_chats":  "Previous Chats",
        "no_chats":    "No previous chats yet",
        "welcome":     "Type your message below to start",
        "placeholder": "Type your message here...",
        "thinking":    "Thinking...",
        "category":    "Category",
        "categories": {
            "wall_chargers": "🔌 Wall Chargers",
            "power_banks":   "🔋 Power Banks",
            "travel_bags":   "🎒 Travel Bags",
            "home_kitchen":  "🏠 Home & Kitchen",
        },
    },
}

# ── Session state initialization ──────────────────────────────────────────────
# It survives Streamlit returns normal variables reset every time
def init_state():
    """Set default values — Arabic is the default language."""
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"                # Default to Arabic
    if "sid" not in st.session_state:
        st.session_state.sid = None                 # Current session ID 
    ## Tracks conversation progress: question count, language, category, stage (clarifying vs recommending)       
    if "chat_state" not in st.session_state:
        st.session_state.chat_state = {"cat": None, "lang": "ar", "stage": "clarifying", "q_count": 0}
    if "messages" not in st.session_state:
        st.session_state.messages = []              # Message shown in currennt chat  
    if "manual_lang" not in st.session_state:
        st.session_state.manual_lang = False
    if "cat_history" not in st.session_state:
        st.session_state.cat_history = []

init_state()

# Auto-create a session on first load so user can chat immediately
if st.session_state.sid is None:
    st.session_state.sid = bot.new_session()

T = TEXT[st.session_state.lang]

# Shows current language on button (AR when Arabic, EN when English)
btn_label = "AR" if st.session_state.lang == "ar" else "EN"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="abg-sidebar-logo">
      <span class="abg-box">ABG</span>
      <span class="abg-fullname">Accord Business Group<br>ShopAssist</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button(T["new_chat"], use_container_width=True):
        st.session_state.sid = bot.new_session()
        st.session_state.messages = []
        st.session_state.manual_lang = False
        st.session_state.chat_state = {"cat": None, "lang": st.session_state.lang, "stage": "clarifying", "q_count": 0}
        st.rerun()

    st.divider()
    st.caption(T["prev_chats"].upper())

    all_sessions = bot.history.get_all_sessions()
    if not all_sessions:
        st.caption(T["no_chats"])
    else:
        for sid, data in reversed(list(all_sessions.items())):
            msgs = data.get("messages", [])
            label = next((m["content"][:28] for m in msgs if m["role"] == "user"), "...")
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.button(f"💬 {label}...", key=f"load_{sid}", use_container_width=True):
                    st.session_state.sid = sid
                    st.session_state.messages = msgs
                    st.session_state.manual_lang = False
                    st.session_state.chat_state = {"cat": None, "lang": st.session_state.lang, "stage": "clarifying", "q_count": 0}
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"del_{sid}"):
                    bot.history.delete_session(sid)
                    if st.session_state.sid == sid:
                        st.session_state.sid = None
                        st.session_state.messages = []
                    st.rerun()

    # ── Charts ────────────────────────────────────────────────────────────────

        # Session stats as metric cards
        st.divider()
        st.caption("💬 SESSION STATS")
        total_msgs = len(st.session_state.messages)
        user_msgs  = sum(1 for m in st.session_state.messages if m["role"] == "user")
        col1, col2 = st.columns(2)
        col1.metric("Messages", total_msgs)
        col2.metric("Queries", user_msgs)

    # Language button at bottom using CSS class
    st.markdown('<div class="lang-fixed">', unsafe_allow_html=True)
    if st.button(btn_label, key="lang_btn"):
        st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
        st.session_state.manual_lang = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0F2557 0%,#2563EB 100%);border-radius:16px 16px 0 0;padding:36px 32px 32px;text-align:center;">
  <svg width="110" height="110" viewBox="0 0 90 90" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-bottom:14px;">
    <line x1="45" y1="6" x2="45" y2="20" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
    <circle cx="45" cy="4" r="5" fill="#00D4FF"/>
    <rect x="14" y="20" width="62" height="42" rx="16" fill="white" opacity="0.95"/>
    <circle cx="32" cy="41" r="7" fill="#0F2557"/>
    <circle cx="58" cy="41" r="7" fill="#0F2557"/>
    <circle cx="32" cy="41" r="3.5" fill="#00D4FF"/>
    <circle cx="58" cy="41" r="3.5" fill="#00D4FF"/>
    <path d="M33 62 L45 76 L57 62" fill="white" opacity="0.95"/>
    <rect x="6" y="30" width="8" height="18" rx="4" fill="white" opacity="0.6"/>
    <rect x="76" y="30" width="8" height="18" rx="4" fill="white" opacity="0.6"/>
  </svg>
  <div style="font-size:11px;font-weight:600;color:rgba(255,255,255,0.6);letter-spacing:3px;margin-bottom:8px;">ACCORD BUSINESS GROUP</div>
  <div style="font-size:30px;font-weight:700;color:#ffffff;margin-bottom:8px;letter-spacing:-0.5px;">ABG ShopAssist Chatbot</div>
  <div style="font-size:15px;color:rgba(255,255,255,0.8);">{T['subtitle']}</div>
</div>
""", unsafe_allow_html=True)

# ── Chat messages ─────────────────────────────────────────────────────────────
st.markdown("""<div style="background:#ffffff;border-left:1px solid #D1DCF5;border-right:1px solid #D1DCF5;border-bottom:1px solid #D1DCF5;border-radius:0 0 16px 16px;padding:28px 40px 20px;min-height:60px;">""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown(f'<div style="text-align:center;padding:40px 0 20px;font-size:15px;color:#94A3B8;">{T["welcome"]}</div>', unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        css = "user-bubble" if msg["role"] == "user" else "bot-bubble"
        st.markdown(f'<div class="{css}">{msg["content"]}</div>', unsafe_allow_html=True)
    cat = st.session_state.chat_state.get("cat")
    if cat and cat != "unknown":
        cat_label = T["categories"].get(cat, cat)
        st.markdown(f'<div class="cat-badge">{T["category"]}: {cat_label}</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input(T["placeholder"])

# Inject JS to force RTL direction inside the sandboxed chat input iframe
if st.session_state.lang == "ar":
    st.components.v1.html("""
    <script>
    function setRTL() {
        const frames = window.parent.document.querySelectorAll('iframe');
        frames.forEach(f => {
            try {
                const ta = f.contentDocument.querySelector('textarea');
                if (ta) {
                    ta.style.direction = 'rtl';
                    ta.style.textAlign = 'right';
                }
            } catch(e) {}
        });
        const ta = window.parent.document.querySelector('[data-testid="stChatInput"] textarea');
        if (ta) {
            ta.style.direction = 'rtl';
            ta.style.textAlign = 'right';
        }
    }
    setRTL();
    setTimeout(setRTL, 300);
    setTimeout(setRTL, 800);
    </script>
    """, height=0)

if user_input:
    if not st.session_state.manual_lang:
        st.session_state.lang = "ar" if any("\u0600" <= c <= "\u06FF" for c in user_input) else "en"
    st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)
    with st.spinner(T["thinking"]):
        reply = bot.chat(st.session_state.sid, user_input, st.session_state.chat_state)

    # Track detected category for charts
    cat = st.session_state.chat_state.get("cat")
    if cat and cat != "unknown":
        st.session_state.cat_history.append(cat)
    st.markdown(f'<div class="bot-bubble">{reply}</div>', unsafe_allow_html=True)
    st.session_state.messages = bot.history.get_messages(st.session_state.sid)
    st.rerun()