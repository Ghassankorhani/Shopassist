import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from config import cfg
from rag import RAGPipeline

log = logging.getLogger(__name__)

# Keywords used to detect which product category the user is asking for
CATEGORY_KEYWORDS = {
    "wall_chargers": [
        # English
        "charger", "wall charger", "adapter", "plug", "watt", "usb",
        "fast charge", "quick charge", "gan", "power adapter", "outlet",
        "charging brick", "wall plug", "socket", "usb-c", "usb-a",
        # Arabic
        "شاحن", "محول", "مشحن", "شاحن حائط", "مقبس", "كهرباء",
    ],
    "power_banks": [
        # English
        "power bank", "portable charger", "battery pack", "portable battery",
        "battery", "mah", "charge on the go", "outdoor charging", "solar",
        "backup battery", "external battery", "pocket charger", "travel charger",
        "camping", "hiking", "outdoor", "off grid", "wireless charging",
        # Arabic
        "باور بنك", "بطارية", "شاحن محمول", "بطارية محمولة", "شحن متنقل",
    ],
    "travel_bags": [
        # English
        "bag", "backpack", "luggage", "carry-on", "duffle", "sling",
        "travel bag", "laptop bag", "school bag", "gym bag", "tote",
        "handbag", "shoulder bag", "hiking bag", "overnight bag",
        "weekend bag", "anti theft", "waterproof bag",
        # Arabic
        "حقيبة", "شنطة", "ظهرية", "حقيبة سفر", "حقيبة لابتوب",
        "حقيبة ظهر", "شنطة سفر",
    ],
    "home_kitchen": [
        # English
        "kitchen", "storage", "mug", "bottle", "organizer", "lunch",
        "food", "container", "water bottle", "lunch box", "spice",
        "cutting board", "laundry", "basket", "dish", "drying rack",
        "drawer", "bamboo", "ceramic", "stainless", "meal prep",
        # Arabic
        "مطبخ", "منزل", "تخزين", "كوب", "زجاجة", "طعام",
        "حاوية", "غداء", "تنظيم", "مطبخ منزلي",
    ],
}

# Keywords that signal Claude is giving a final recommendation
RECOMMENDATION_SIGNALS = [
    "i recommend", "i suggest", "best option", "perfect choice", "great fit",
    "ideal for", "you should go with", "my recommendation", "best match",
    "perfect for you", "i would recommend", "great choice", "top pick",
    "أنصحك", "أقترح", "الخيار الأفضل", "مثالي", "الأنسب", "أوصي",
]

#Sent to Claude on every message
PROMPT = """أنت ShopAssist، مساعد تسوق ذكي يساعد العملاء في اكتشاف المنتجات المناسبة.
You are ShopAssist, a smart shopping assistant that helps customers find the right product.

## القواعد الصارمة / Strict Rules
- اكتشف لغة العميل وأجب بنفس اللغة دائماً (عربي أو إنجليزي فقط).
- Detect the customer's language and always reply in the same language (Arabic or English only).
- لا تعطي توصية فوراً — اسأل سؤالاً واحداً في كل مرة.
- Never recommend immediately — ask ONE question at a time.
- اسأل 3 أسئلة كحد أقصى قبل التوصية النهائية.
- Ask at most 3 questions before giving the final recommendation.
- **وصِّ فقط بمنتجات موجودة حرفياً في قائمة المنتجات أدناه. لا تخترع منتجات.**
- **ONLY recommend products that are EXPLICITLY listed in the catalog below. NEVER invent products.**
- إذا طلب العميل منتجاً غير موجود، أخبره بأدب واقترح أقرب منتج موجود.
- If the customer asks for something not in the catalog, politely say so and suggest the closest match.
- For outdoor or camping use → SolarTrail 15K and RuggedPro 20K are perfect power bank matches.
- For travel bags → recommend based on trip type (day trip, overnight, hiking, city).
- For kitchen items → recommend based on the specific item type mentioned.
- NEVER say a product does not exist if it appears in the catalog context below.

## قائمة المنتجات المتاحة فقط / Available Catalog ONLY
{catalog}

## سجل المحادثة / Conversation History
{history}

## رسالة العميل / Customer Message
{message}
"""

##Handles savings and loads the conv to JSON file
class ChatHistory:
    # Create the folder if it doesn't exist, and load existing history or start fresh  
    def __init__(self):
        # Ensure the data directory and history file exist
        Path(cfg.history_file).parent.mkdir(parents=True, exist_ok=True)
        self.path = Path(cfg.history_file)
        self.data: dict = self._load()
    
    def _load(self) -> dict:
        """Load existing history from JSON file, or return empty dict."""
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        """Persist the current history to disk."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def new_session(self) -> str:
        """Create a new session with a unique ID and save it."""
        sid = str(uuid.uuid4())[:8]
        self.data[sid] = {
            "created_at": datetime.now().isoformat(),
            "messages": [],
        }
        self._save()
        return sid

    def add(self, sid: str, role: str, content: str):
        """Append a message to a session and save."""
        self.data[sid]["messages"].append({
            "role": role,
            "content": content,
            "time": datetime.now().isoformat(),
        })
        self._save()

    def get_messages(self, sid: str) -> list:
        """Return all messages for a session."""
        return self.data.get(sid, {}).get("messages", [])

    def get_all_sessions(self) -> dict:
        """Return all sessions (used by UI to list history)."""
        return self.data

    def delete_session(self, sid: str):
        """Remove a session from history."""
        self.data.pop(sid, None)
        self._save()

    def format_for_prompt(self, sid: str) -> str:
        """Format the last 10 messages as a readable string for the LLM prompt."""
        msgs = self.get_messages(sid)[-10:]
        lines = []
        for m in msgs:
            speaker = "العميل/Customer" if m["role"] == "user" else "ShopAssist"
            lines.append(f"{speaker}: {m['content']}")
        return "\n".join(lines) if lines else "لا توجد رسائل سابقة. / No previous messages."

#Language detection, RAG search and claude calls all happen here
class Chatbot:

    def __init__(self, rag: RAGPipeline):
        self.rag = rag
        self.history = ChatHistory()
        # Connect to Claude via LangChain — reads API key from config
        self.llm = ChatAnthropic(
            model=cfg.model,
            api_key=cfg.anthropic_api_key,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
        )

    def new_session(self) -> str:
        """Start a fresh conversation session."""
        return self.history.new_session()

    def chat(self, sid: str, user_msg: str, session_state: dict) -> str:
        """
        Process a user message and return the assistant's reply.
        Updates session_state (category, language, stage, question count).
        """
        # Detect language
        session_state["lang"] = "ar" if self._is_arabic(user_msg) else "en"

        # Detect category — only update if not already correctly identified
        if not session_state.get("cat") or session_state.get("cat") == "unknown":
            detected = self._classify(user_msg)
            if detected != "unknown":
                session_state["cat"] = detected

        # Retrieve relevant products chunks from ChromaDB
        docs = self.rag.retrieve(user_msg, cat=session_state.get("cat"))
        catalog = "\n\n".join(d.page_content for d in docs)

        # Build the prompt with history and catalog context
        prompt = PROMPT.format(
            catalog=catalog,
            history=self.history.format_for_prompt(sid),
            message=user_msg,
        )

        # Call Claude — only LLM call in this project
        reply = self.llm.invoke([HumanMessage(content=prompt)]).content.strip()

        # Detect if Claude is still  recommending 
        session_state["stage"] = self._detect_stage(reply, session_state.get("q_count", 0))
        if session_state["stage"] == "clarifying":
            session_state["q_count"] = session_state.get("q_count", 0) + 1

        # Save both messages to history
        self.history.add(sid, "user", user_msg)
        self.history.add(sid, "assistant", reply)

        return reply

    def _classify(self, text: str) -> str:
        """Detect product category from user message using keyword matching."""
        t = text.lower()
        scores = {
            cat: sum(1 for kw in kws if kw in t)
            for cat, kws in CATEGORY_KEYWORDS.items()
        }
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else "unknown"

    def _is_arabic(self, text: str) -> bool:
        """Check if the message contains Arabic characters."""
        return any("\u0600" <= ch <= "\u06FF" for ch in text)
    #Force recommendation after 3 questions or if certain signals are detected in the reply
    def _detect_stage(self, reply: str, q_count: int) -> str:
        """Determine if Claude is still asking questions or ready to recommend."""
        if q_count >= 3:
            return "recommendation"
        if any(sig in reply.lower() for sig in RECOMMENDATION_SIGNALS):
            return "recommendation"
        return "clarifying"