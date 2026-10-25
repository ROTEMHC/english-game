import io
import json
import os
from pathlib import Path
import random
import re
import urllib.parse

import anthropic
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="הלומדה הקסומה באנגלית", page_icon="🌟", layout="centered"
)

# ---------------------------------------------------------------------------
# נתונים: לכל קטגוריה - (עברית, אנגלית, אימוג'י)
# ---------------------------------------------------------------------------
CATEGORIES = {
    "letters": {
        "name": "אותיות",
        "emoji": "🔤",
        "items": [
            ("תפוח", "Apple", "🍎"), ("כדור", "Ball", "⚽"),
            ("חתול", "Cat", "🐱"), ("כלב", "Dog", "🐶"),
            ("פיל", "Elephant", "🐘"), ("דג", "Fish", "🐟"),
            ("ג'ירפה", "Giraffe", "🦒"), ("כובע", "Hat", "🎩"),
            ("גלידה", "Ice cream", "🍦"), ("מיץ", "Juice", "🧃"),
            ("עפיפון", "Kite", "🪁"), ("אריה", "Lion", "🦁"),
            ("ירח", "Moon", "🌙"), ("קן", "Nest", "🪺"),
            ("תפוז", "Orange", "🍊"), ("חזיר", "Pig", "🐷"),
            ("מלכה", "Queen", "👸"), ("ארנב", "Rabbit", "🐰"),
            ("שמש", "Sun", "☀️"), ("עץ", "Tree", "🌳"),
            ("מטרייה", "Umbrella", "☂️"), ("כינור", "Violin", "🎻"),
            ("אבטיח", "Watermelon", "🍉"), ("קסילופון", "Xylophone", "🎶"),
            ("יו-יו", "Yo-yo", "🪀"), ("זברה", "Zebra", "🦓"),
        ],
    },
    "animals": {
        "name": "חיות",
        "emoji": "🦁",
        "items": [
            ("כלב", "Dog", "🐶"), ("חתול", "Cat", "🐱"),
            ("פיל", "Elephant", "🐘"), ("אריה", "Lion", "🦁"),
            ("סוס", "Horse", "🐴"), ("קוף", "Monkey", "🐵"),
            ("פרפר", "Butterfly", "🦋"), ("ג'ירפה", "Giraffe", "🦒"),
            ("דולפין", "Dolphin", "🐬"), ("פרה", "Cow", "🐮"),
            ("צפרדע", "Frog", "🐸"), ("תרנגולת", "Chicken", "🐔"),
            ("ארנב", "Rabbit", "🐰"), ("דב", "Bear", "🐻"),
            ("נמר", "Tiger", "🐯"), ("זברה", "Zebra", "🦓"),
            ("פינגווין", "Penguin", "🐧"), ("ינשוף", "Owl", "🦉"),
            ("שועל", "Fox", "🦊"), ("ברווז", "Duck", "🦆"),
            ("חזיר", "Pig", "🐷"), ("כבשה", "Sheep", "🐑"),
            ("עז", "Goat", "🐐"), ("עכבר", "Mouse", "🐭"),
            ("נחש", "Snake", "🐍"), ("צב", "Turtle", "🐢"),
            ("דג", "Fish", "🐟"), ("קנגורו", "Kangaroo", "🦘"),
            ("פנדה", "Panda", "🐼"), ("לווייתן", "Whale", "🐋"),
            ("תנין", "Crocodile", "🐊"), ("דבורה", "Bee", "🐝"),
        ],
    },
    "colors": {
        "name": "צבעים",
        "emoji": "🎨",
        # צבעים: פריט רביעי = קוד הצבע, כדי להציג את הצבע עצמו
        "items": [
            ("אדום", "Red", "🔴", "#E53935"), ("כחול", "Blue", "🔵", "#1E63D6"),
            ("צהוב", "Yellow", "🟡", "#FFD600"), ("ירוק", "Green", "🟢", "#2E9E44"),
            ("סגול", "Purple", "🟣", "#8E3FC9"), ("כתום", "Orange", "🟠", "#FF8A00"),
            ("ורוד", "Pink", "🩷", "#FF77B7"), ("שחור", "Black", "⚫", "#1B1B1B"),
            ("לבן", "White", "⚪", "#FFFFFF"), ("חום", "Brown", "🟤", "#7B4A26"),
            ("אפור", "Gray", "🩶", "#9E9E9E"), ("תכלת", "Light blue", "🩵", "#7FD3FF"),
            ("זהב", "Gold", "🥇", "#D4AF37"), ("כסף", "Silver", "🥈", "#C0C0C0"),
            ("טורקיז", "Turquoise", "💎", "#1CC7C1"), ("בורדו", "Maroon", "🍷", "#800020"),
            ("בז'", "Beige", "🏖️", "#E8D8B8"), ("כחול כהה", "Navy", "🌌", "#1A2A6C"),
            ("ירוק בהיר", "Light green", "🍏", "#9BE37A"), ("לילך", "Lilac", "💜", "#C8A2C8"),
        ],
    },
    "objects": {
        "name": "חפצים",
        "emoji": "🧸",
        "items": [
            ("דובי", "Teddy bear", "🧸"), ("מפתח", "Key", "🔑"),
            ("שעון", "Clock", "⏰"), ("טלפון", "Phone", "📱"),
            ("מיטה", "Bed", "🛏️"), ("דלת", "Door", "🚪"),
            ("כוס", "Cup", "🥤"), ("מתנה", "Gift", "🎁"),
            ("בלון", "Balloon", "🎈"), ("נעל", "Shoe", "👟"),
        ],
    },
    "family": {
        "name": "בני משפחה",
        "emoji": "👨‍👩‍👧",
        "items": [
            ("אמא", "Mom", "👩"), ("אבא", "Dad", "👨"),
            ("אח", "Brother", "👦"), ("אחות", "Sister", "👧"),
            ("סבא", "Grandpa", "👴"), ("סבתא", "Grandma", "👵"),
            ("תינוק", "Baby", "👶"), ("משפחה", "Family", "👨‍👩‍👧"),
        ],
    },
    "classroom": {
        "name": "כיתה",
        "emoji": "🎒",
        "items": [
            ("ספר", "Book", "📕"), ("עיפרון", "Pencil", "✏️"),
            ("תיק", "Bag", "🎒"), ("כיסא", "Chair", "🪑"),
            ("מספריים", "Scissors", "✂️"), ("סרגל", "Ruler", "📏"),
            ("מחשב", "Computer", "💻"), ("צבע", "Crayon", "🖍️"),
            ("מחברת", "Notebook", "📓"), ("מורה", "Teacher", "🧑‍🏫"),
        ],
    },
    "nature": {
        "name": "טבע",
        "emoji": "🌳",
        "items": [
            ("שמש", "Sun", "☀️"), ("פרח", "Flower", "🌸"),
            ("עץ", "Tree", "🌳"), ("ים", "Sea", "🌊"),
            ("ענן", "Cloud", "☁️"), ("גשם", "Rain", "🌧️"),
            ("ירח", "Moon", "🌙"), ("הר", "Mountain", "⛰️"),
            ("כוכב", "Star", "⭐"), ("קשת", "Rainbow", "🌈"),
        ],
    },
    "food": {
        "name": "אוכל",
        "emoji": "🍕",
        "items": [
            ("תפוח", "Apple", "🍎"), ("בננה", "Banana", "🍌"),
            ("לחם", "Bread", "🍞"), ("גבינה", "Cheese", "🧀"),
            ("ביצה", "Egg", "🥚"), ("פיצה", "Pizza", "🍕"),
            ("חלב", "Milk", "🥛"), ("עוגה", "Cake", "🍰"),
            ("ענבים", "Grapes", "🍇"), ("גזר", "Carrot", "🥕"),
        ],
    },
    "transport": {
        "name": "תחבורה",
        "emoji": "🚗",
        "items": [
            ("מכונית", "Car", "🚗"), ("אוטובוס", "Bus", "🚌"),
            ("מטוס", "Airplane", "✈️"), ("אופניים", "Bicycle", "🚲"),
            ("רכבת", "Train", "🚂"), ("ספינה", "Ship", "🚢"),
            ("מסוק", "Helicopter", "🚁"), ("טיל", "Rocket", "🚀"),
        ],
    },
    "body": {
        "name": "גוף",
        "emoji": "🖐️",
        "items": [
            ("עין", "Eye", "👁️"), ("אוזן", "Ear", "👂"),
            ("אף", "Nose", "👃"), ("פה", "Mouth", "👄"),
            ("יד", "Hand", "✋"), ("רגל", "Foot", "🦶"),
            ("שן", "Tooth", "🦷"), ("שיער", "Hair", "💇"),
        ],
    },
}

# מילים נוספות לכל אות (בנוסף למילים מכל הקטגוריות)
LETTER_EXTRA = [
    ("דב", "Bear", "🐻"), ("ציפור", "Bird", "🐦"), ("סירה", "Boat", "⛵"),
    ("עוגייה", "Cookie", "🍪"), ("ברווז", "Duck", "🦆"), ("דרקון", "Dragon", "🐉"),
    ("נשר", "Eagle", "🦅"), ("שועל", "Fox", "🦊"), ("אש", "Fire", "🔥"),
    ("רוח רפאים", "Ghost", "👻"), ("גיטרה", "Guitar", "🎸"), ("בית", "House", "🏠"),
    ("לב", "Heart", "❤️"), ("איגלו", "Igloo", "🛖"), ("חרק", "Insect", "🐛"),
    ("מדוזה", "Jellyfish", "🪼"), ("ג'ינס", "Jeans", "👖"), ("קנגורו", "Kangaroo", "🦘"),
    ("מלך", "King", "🤴"), ("לימון", "Lemon", "🍋"), ("עלה", "Leaf", "🍃"),
    ("עכבר", "Mouse", "🐭"), ("פטרייה", "Mushroom", "🍄"), ("לילה", "Night", "🌃"),
    ("ינשוף", "Owl", "🦉"), ("תמנון", "Octopus", "🐙"), ("פינגווין", "Penguin", "🐧"),
    ("עיפרון", "Pencil", "✏️"), ("שאלה", "Question", "❓"), ("שמיכה", "Quilt", "🛏️"),
    ("רובוט", "Robot", "🤖"), ("טבעת", "Ring", "💍"), ("נחש", "Snake", "🐍"),
    ("כוכב ים", "Starfish", "⭐"), ("נמר", "Tiger", "🐯"), ("עגבנייה", "Tomato", "🍅"),
    ("חד קרן", "Unicorn", "🦄"), ("ואן", "Van", "🚐"), ("הר געש", "Volcano", "🌋"),
    ("לווייתן", "Whale", "🐋"), ("שעון יד", "Watch", "⌚"), ("צילום רנטגן", "X-ray", "🩻"),
    ("קופסה", "Box", "📦"), ("יוגורט", "Yogurt", "🥣"), ("צהוב", "Yellow", "💛"),
    ("גן חיות", "Zoo", "🦁"), ("רוכסן", "Zipper", "🤐"), ("אפס", "Zero", "0️⃣"),
]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def unpack(item):
  """(עברית, אנגלית, אימוג'י, צבע או None)"""
  heb, eng, emo, *rest = item
  return heb, eng, emo, (rest[0] if rest else None)


# מילון חיפוש מהיר עברית -> (אנגלית, אימוג'י) למשחק ההקלדה
LOCAL_DICT = {
    unpack(it)[0]: unpack(it)[1:3]
    for cat in CATEGORIES.values()
    for it in cat["items"]
}

GAMES = {
    "cards": ("🖼️", "כרטיסיות תמונה", "לוחצים על תמונה ושומעים בעברית ובאנגלית"),
    "find": ("🔍", "איפה התמונה?", "שומעים מילה באנגלית ומוצאים את התמונה"),
    "type": ("⌨️", "מקלידים בעברית", "מקלידים מילה בעברית ושומעים אותה באנגלית"),
    "missing": ("🧩", "האותיות החסרות", "מרכיבים מילה באנגלית מהאותיות החסרות"),
    "explore": ("🔤", "כל אות והמילים שלה", "בוחרים אות ורואים מילים שמתחילות בה"),
    "abc": ("🚂", "תרגול כל האותיות A-Z", "עוברים על כל האותיות לפי הסדר"),
    "find_letter": ("🔍", "איפה האות?", "שומעים אות באנגלית ומוצאים אותה"),
}


def games_for(age, category):
  if category == "letters":
    return (["explore", "abc", "find_letter"] if age == "small"
            else ["explore", "abc", "find_letter", "missing", "type"])
  return ["cards", "find"] if age == "small" else ["cards", "type", "missing", "find"]


# ---------------------------------------------------------------------------
# אוצר מילים מורחב בעזרת Claude (AI) - נשמר לקובץ כדי שיגדל עם הזמן
# ---------------------------------------------------------------------------
EXTRA_FILE = Path(__file__).with_name("extra_words.json")
WORD_SCHEMA = {
    "type": "object",
    "properties": {
        "words": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hebrew": {"type": "string"},
                    "english": {"type": "string"},
                    "emoji": {"type": "string"},
                    "hex": {"type": "string"},
                },
                "required": ["hebrew", "english", "emoji", "hex"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["words"],
    "additionalProperties": False,
}


def load_extra():
  try:
    return json.loads(EXTRA_FILE.read_text(encoding="utf-8"))
  except Exception:
    return {}


def save_extra(data):
  try:
    EXTRA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                          encoding="utf-8")
  except Exception:
    pass


def secret(name):
  """מפתח מ-.streamlit/secrets.toml או ממשתני הסביבה (לא חובה)."""
  try:
    key = st.secrets.get(name)
  except Exception:
    key = None
  return (key or os.environ.get(name) or "").strip()


def claude_key():
  return secret("ANTHROPIC_API_KEY")


def gemini_key():
  return secret("GEMINI_API_KEY")


def _ask_gemini(system, prompt):
  """Gemini של Google - יש מכסה חינמית (מפתח מ-aistudio.google.com)."""
  from google import genai
  from google.genai import types

  client = genai.Client(api_key=gemini_key())  # חייב משתנה, אחרת הוא נסגר
  response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=prompt,
      config=types.GenerateContentConfig(
          system_instruction=system,
          response_mime_type="application/json",
      ),
  )
  return response.text


def _ask_claude(system, prompt):
  response = anthropic.Anthropic(api_key=claude_key()).beta.messages.create(
      model="claude-opus-5-5",
      max_tokens=4000,
      betas=["server-side-fallback-2026-07-01"],
      fallbacks="default",
      output_config={
          "effort": "low",
          "format": {"type": "json_schema", "schema": WORD_SCHEMA},
      },
      system=system,
      messages=[{"role": "user", "content": prompt}],
  )
  if response.stop_reason == "refusal":
    raise RuntimeError("refused")
  return "".join(b.text for b in response.content if b.type == "text")


def _ask_free_ai(system, prompt):
  """AI חינמי ללא מפתח והרשמה (Pollinations)."""
  r = requests.post(
      "https://text.pollinations.ai/openai",
      json={
          "model": "openai-fast",
          "messages": [{"role": "system", "content": system},
                       {"role": "user", "content": prompt}],
          "response_format": {"type": "json_object"},
          "reasoning_effort": "low",
      },
      timeout=90,
  )
  if r.status_code in (402, 429):  # בחינם: תשובה אחת כל 30 שניות
    raise FreeLimitError()
  r.raise_for_status()
  return r.json()["choices"][0]["message"]["content"]


class FreeLimitError(Exception):
  pass


class TranslationUnavailable(Exception):
  pass


@st.cache_data(show_spinner=False)
def _ai_words(request, age, avoid):
  ages = "1-4 (very basic, concrete words)" if age == "small" else "5-8"
  system = (
      "You supply vocabulary for an English-learning game for Hebrew-speaking"
      f" children aged {ages}. Only friendly, child-appropriate, concrete"
      " words that can be shown with a single emoji."
  )
  prompt = (
      f"Give 12 new words for: {request}.\n"
      'Answer with JSON only: {"words": [{"hebrew": "", "english": "",'
      ' "emoji": "", "hex": ""}]}\n'
      "hebrew = the everyday Hebrew word (no niqqud); english = the English"
      " word; emoji = one emoji that best shows it; hex = for colors, the"
      " color's hex code like #FF0000, otherwise an empty string.\n"
      f"Do not repeat any of these: {', '.join(avoid)}"
  )
  # Gemini (חינמי עם מפתח) > Claude (בתשלום) > Pollinations (חינמי בלי מפתח)
  if gemini_key():
    ask, trusted_hebrew = _ask_gemini, True
  elif claude_key():
    ask, trusted_hebrew = _ask_claude, True
  else:
    ask, trusted_hebrew = _ask_free_ai, False
  use_claude = trusted_hebrew
  text = ask(system, prompt).strip().strip("`").removeprefix("json")
  raw = json.loads(text)["words"]
  if not trusted_hebrew:
    # העברית של ה-AI החינמי לא אמינה - מתרגמים עם Google
    hebrew = translate_words_to_hebrew(
        [str(w.get("english", "")).strip().capitalize() for w in raw])
    if not hebrew:
      raise TranslationUnavailable()
  words = []
  for w in raw:
    eng = str(w.get("english", "")).strip().capitalize()
    heb = (str(w.get("hebrew", "")).strip() if use_claude
           else hebrew.get(eng, ""))
    hexc = str(w.get("hex") or "").strip()
    if "color" not in request or not re.fullmatch(r"#[0-9A-Fa-f]{6}", hexc):
      hexc = None
    if eng and heb and eng not in avoid:
      words.append((heb, eng, str(w.get("emoji") or "✨"), hexc))
  if not words:
    raise ValueError("no words")
  return words


def ai_button(store_key, request, existing, label="✨ עוד מילים מ-AI"):
  """כפתור שמבקש מ-Claude מילים חדשות ושומר אותן תחת store_key."""
  if not st.button(label, key=f"ai_{store_key}", use_container_width=True):
    return
  avoid = tuple(sorted({unpack(it)[1] for it in existing}))
  with st.spinner("ה-AI מחפש מילים חדשות... 🤖✨"):
    try:
      new = _ai_words(request, ss.age, avoid)
    except anthropic.AuthenticationError:
      st.error("🔑 מפתח ה-API של Claude לא תקין. בדקו את ANTHROPIC_API_KEY")
      return
    except TranslationUnavailable:
      st.warning("🌐 התרגום לעברית לא זמין כרגע - נסו שוב בעוד כמה דקות")
      return
    except FreeLimitError:
      st.warning("⏳ ה-AI החינמי נותן תשובה אחת כל 30 שניות - חכו רגע ונסו שוב")
      return
    except Exception as e:
      msg = str(e)
      if "API key" in msg or "API_KEY" in msg or "PERMISSION_DENIED" in msg:
        st.error("🔑 מפתח ה-AI לא תקין - בדקו את המפתח בקובץ .streamlit/secrets.toml")
        return
      if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        st.warning("⏳ נגמרה המכסה החינמית לרגע - חכו דקה ונסו שוב")
        return
      st.error("🌐 ה-AI לא זמין כרגע, נסו שוב בעוד רגע"
               f" (פרטים: {type(e).__name__})")
      return
  data = load_extra()
  data.setdefault(store_key, []).extend([list(w) for w in new])
  save_extra(data)
  st.success(f"🎉 נוספו {len(new)} מילים חדשות!")
  st.rerun()


def extra_items(store_key):
  return [tuple(w) for w in load_extra().get(store_key, [])]


def letter_words(letter):
  """כל המילים שמתחילות באות - מכל הקטגוריות, מהרשימה הנוספת ומה-AI."""
  seen, result = set(), []
  pool = [it for c in CATEGORIES.values() for it in c["items"]]
  pool += LETTER_EXTRA + extra_items(f"letter_{letter}")
  for key in CATEGORIES:
    pool += extra_items(key)
  for it in pool:
    heb, eng, emo, hexc = unpack(it)
    if eng[:1].upper() == letter and eng not in seen:
      seen.add(eng)
      result.append(it)
  return result


# ---------------------------------------------------------------------------
# עיצוב
# ---------------------------------------------------------------------------
def letters_background():
  """אריח SVG עם אותיות אנגליות צבעוניות לרקע."""
  rnd = random.Random(7)
  colors = ["#FF6B6B", "#4D96FF", "#FFD93D", "#6BCB77", "#B983FF", "#FF9F45"]
  parts = []
  for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    x, y = (i % 6) * 70 + rnd.randint(5, 30), (i // 6) * 75 + rnd.randint(35, 55)
    parts.append(
        f'<text x="{x}" y="{y}" font-size="{rnd.randint(30, 46)}" '
        f'font-family="Arial Rounded MT Bold,Arial" font-weight="bold" '
        f'fill="{rnd.choice(colors)}" opacity="0.22" '
        f'transform="rotate({rnd.randint(-25, 25)} {x} {y})">{ch}</text>'
    )
  svg = (
      '<svg xmlns="http://www.w3.org/2000/svg" width="420" height="380">'
      + "".join(parts)
      + "</svg>"
  )
  return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Varela+Round&display=swap');
html, body, [class*="css"], .stApp, button, input {{ font-family: 'Varela Round', sans-serif; }}
.stApp {{
  background-color: #FFF8E7;
  background-image: url("{letters_background()}");
}}
.block-container {{
  direction: rtl; text-align: right;
  background: rgba(255,255,255,0.88);
  border-radius: 28px; margin-top: 2rem; padding: 2rem 2rem 3rem;
  box-shadow: 0 8px 30px rgba(0,0,0,0.08);
}}
h1, h2, h3 {{ text-align: center; color: #3D348B; }}
.stButton button {{
  font-size: 1.35rem; min-height: 3.6rem; border-radius: 22px;
  border: 3px solid #FFD93D; background: #FFFDF5; transition: transform .1s;
}}
.stButton button p {{ font-size: 1.35rem; }}
.stButton button:hover {{ transform: scale(1.04); border-color: #FF9F45; }}
.stButton button[kind="primary"] {{ background: #FF6B6B; border-color: #FF6B6B; color: white; }}
.big-card {{
  text-align: center; background: #FFF3C4; border-radius: 28px;
  padding: 1rem; margin: .5rem 0 1rem; border: 4px dashed #FFB703;
}}
.big-card .emo {{ font-size: 110px; line-height: 1.1; }}
.big-card .eng {{ font-size: 46px; color: #3D348B; direction: ltr; font-weight: bold; }}
.big-card .heb {{ font-size: 30px; color: #555; }}
.puzzle {{
  direction: ltr; text-align: center; font-size: 52px; letter-spacing: 12px;
  font-family: 'Courier New', monospace; font-weight: bold; color: #3D348B;
}}
.puzzle .gap {{ color: #FF6B6B; }}
.stTextInput input {{ font-size: 1.4rem; text-align: center; }}
</style>
""",
    unsafe_allow_html=True,
)

HERO = """
<style>
@keyframes floaty { 0%,100% { transform: translateY(0) rotate(-8deg);} 50% { transform: translateY(-14px) rotate(8deg);} }
.hero { position: relative; text-align: center; }
.hero .fl { position: absolute; font-size: 44px; font-weight: bold; animation: floaty 3s ease-in-out infinite; font-family: Arial Rounded MT Bold, Arial; }
.hero h1 { font-size: 2.6rem; color: #3D348B; margin: .2rem 0; font-family: 'Varela Round', sans-serif; }
.hero p { font-size: 1.3rem; color: #555; font-family: 'Varela Round', sans-serif; }
</style>
<div class="hero">
  <span class="fl" style="top:10px;left:4%;color:#FF6B6B">A</span>
  <span class="fl" style="top:120px;left:0;color:#4D96FF;animation-delay:.5s">B</span>
  <span class="fl" style="top:20px;right:4%;color:#6BCB77;animation-delay:1s">C</span>
  <span class="fl" style="top:140px;right:0;color:#B983FF;animation-delay:1.5s">D</span>
  <span class="fl" style="top:250px;left:6%;color:#FF9F45;animation-delay:.8s">E</span>
  <span class="fl" style="top:250px;right:6%;color:#FFD93D;animation-delay:1.2s">F</span>
  <img src="{drawing}" style="width:100%;max-width:420px">
  <h1>🌟 הלומדה הקסומה באנגלית 🌟</h1>
  <p>Magical English for Kids — לומדים אנגלית דרך משחק!</p>
</div>
"""

HERO_SVG = """
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
    <!-- קשת -->
    <g fill="none" stroke-width="14">
      <path d="M60 210 A140 140 0 0 1 340 210" stroke="#FF6B6B"/>
      <path d="M74 210 A126 126 0 0 1 326 210" stroke="#FF9F45"/>
      <path d="M88 210 A112 112 0 0 1 312 210" stroke="#FFD93D"/>
      <path d="M102 210 A98 98 0 0 1 298 210" stroke="#6BCB77"/>
      <path d="M116 210 A84 84 0 0 1 284 210" stroke="#4D96FF"/>
      <path d="M130 210 A70 70 0 0 1 270 210" stroke="#B983FF"/>
    </g>
    <!-- שמש מחייכת -->
    <g transform="translate(330 55)">
      <g stroke="#FFB703" stroke-width="6" stroke-linecap="round">
        <line x1="0" y1="-44" x2="0" y2="-34"/><line x1="0" y1="44" x2="0" y2="34"/>
        <line x1="-44" y1="0" x2="-34" y2="0"/><line x1="44" y1="0" x2="34" y2="0"/>
        <line x1="-31" y1="-31" x2="-24" y2="-24"/><line x1="31" y1="31" x2="24" y2="24"/>
        <line x1="31" y1="-31" x2="24" y2="-24"/><line x1="-31" y1="31" x2="-24" y2="24"/>
      </g>
      <circle r="28" fill="#FFD93D"/>
      <circle cx="-9" cy="-5" r="3.5" fill="#3D348B"/><circle cx="9" cy="-5" r="3.5" fill="#3D348B"/>
      <path d="M-10 7 Q0 17 10 7" stroke="#3D348B" stroke-width="3" fill="none" stroke-linecap="round"/>
    </g>
    <!-- עננים -->
    <g fill="#FFFFFF" stroke="#D6E4FF" stroke-width="2">
      <ellipse cx="70" cy="60" rx="38" ry="20"/><ellipse cx="95" cy="50" rx="26" ry="20"/>
      <ellipse cx="200" cy="40" rx="30" ry="15"/><ellipse cx="220" cy="33" rx="20" ry="15"/>
    </g>
    <!-- דשא -->
    <path d="M0 255 Q100 225 200 250 T400 245 V300 H0 Z" fill="#8AD879"/>
    <!-- קוביות ABC -->
    <g font-family="Arial Rounded MT Bold, Arial" font-weight="bold" font-size="40" text-anchor="middle">
      <rect x="120" y="200" width="54" height="54" rx="8" fill="#FF6B6B"/><text x="147" y="242" fill="#fff">A</text>
      <rect x="176" y="200" width="54" height="54" rx="8" fill="#4D96FF"/><text x="203" y="242" fill="#fff">B</text>
      <rect x="232" y="200" width="54" height="54" rx="8" fill="#6BCB77"/><text x="259" y="242" fill="#fff">C</text>
      <rect x="148" y="146" width="54" height="54" rx="8" fill="#FFD93D"/><text x="175" y="188" fill="#fff">D</text>
      <rect x="204" y="146" width="54" height="54" rx="8" fill="#B983FF"/><text x="231" y="188" fill="#fff">E</text>
    </g>
    <!-- בלון -->
    <ellipse cx="50" cy="150" rx="22" ry="27" fill="#FF6B6B"/>
    <path d="M50 177 Q44 200 54 220 Q46 240 52 255" stroke="#888" stroke-width="2" fill="none"/>
    <ellipse cx="42" cy="140" rx="6" ry="9" fill="#fff" opacity=".5"/>
    <!-- פרחים -->
    <g><circle cx="330" cy="262" r="7" fill="#FFD93D"/><circle cx="330" cy="250" r="7" fill="#FF9FB2"/><circle cx="342" cy="262" r="7" fill="#FF9FB2"/><circle cx="318" cy="262" r="7" fill="#FF9FB2"/><circle cx="330" cy="274" r="7" fill="#FF9FB2"/></g>
    <g><circle cx="370" cy="270" r="6" fill="#FFD93D"/><circle cx="370" cy="260" r="6" fill="#B983FF"/><circle cx="380" cy="270" r="6" fill="#B983FF"/><circle cx="360" cy="270" r="6" fill="#B983FF"/><circle cx="370" cy="280" r="6" fill="#B983FF"/></g>
  </svg>
"""
HERO = HERO.replace(
    "{drawing}", "data:image/svg+xml;utf8," + urllib.parse.quote(HERO_SVG.strip())
)


# ---------------------------------------------------------------------------
# כלים: תרגום, שמע, תמונה
# ---------------------------------------------------------------------------
def translate_words_to_hebrew(english_words):
  """מתרגם רשימת מילים בבקשה אחת ל-Google. מחזיר {אנגלית: עברית}."""
  google = GoogleTranslator(source="en", target="iw")
  result = {}
  try:
    lines = google.translate("\n".join(english_words)).split("\n")
    if len(lines) == len(english_words):
      result = dict(zip(english_words, lines))
  except Exception:
    pass
  for eng in english_words:  # מה שלא הצליח - מילה אחת בכל פעם
    if eng not in result:
      try:
        result[eng] = google.translate(eng)
      except Exception:
        pass
  # רק עברית תקינה (בלי אותיות לטיניות)
  return {e: h.strip() for e, h in result.items()
          if h and not re.search(r"[A-Za-z]", h)}


def translate_hebrew_to_english(text):
  try:
    return _translate(text)
  except Exception:
    return None


@st.cache_data(show_spinner=False)
def _translate(text):
  for translator in (
      lambda: GoogleTranslator(source="iw", target="en"),
      lambda: MyMemoryTranslator(source="he-IL", target="en-GB"),
  ):
    try:
      result = translator().translate(text)
      if result:
        return result.capitalize()
    except Exception:
      continue
  raise ValueError("translation failed")


@st.cache_data(show_spinner=False)
def _gtts(text, lang):
  # כישלון זורק חריגה ולכן לא נשמר במטמון - ננסה שוב בפעם הבאה
  buf = io.BytesIO()
  if lang == "en":
    gTTS(text=text, lang="en", tld="us", slow=True).write_to_fp(buf)
  else:
    gTTS(text=text, lang="iw").write_to_fp(buf)
  return buf.getvalue()


def tts_bytes(text, lang):
  try:
    return _gtts(text, lang)
  except Exception:
    return None


def speak(*parts):
  """מנגן רצף של (טקסט, שפה) - קבצי MP3 מחוברים לנגן אחד."""
  chunks = [tts_bytes(t, l) for t, l in parts]
  chunks = [c for c in chunks if c]
  if chunks:
    st.audio(b"".join(chunks), format="audio/mp3", autoplay=True)
    return
  # גיבוי: הקראה בעזרת מנוע הדיבור של הדפדפן
  langs = {"en": "en-US", "iw": "he-IL"}
  utterances = json.dumps([[t, langs[l]] for t, l in parts], ensure_ascii=False)
  components.html(
      f"""<!-- {random.random()} -->
<button id="b" style="font-size:20px;border-radius:16px;padding:6px 16px;
 border:3px solid #FFD93D;background:#FFFDF5;cursor:pointer">🔊 שמעו שוב</button>
<script>
const parts = {utterances};
function say() {{
  const s = window.speechSynthesis; s.cancel();
  for (const [text, lang] of parts) {{
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang; u.rate = 0.8; s.speak(u);
  }}
}}
document.getElementById('b').onclick = say;
say();
</script>""",
      height=50,
  )


@st.cache_data(show_spinner=False)
def find_image(english_word):
  """מחפש תמונה בוויקיפדיה למילה שהוקלדה חופשי."""
  try:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(
        english_word
    )
    r = requests.get(url, timeout=6, headers={"User-Agent": "KidsEnglishGame/1.0"})
    if r.ok:
      return r.json().get("thumbnail", {}).get("source")
  except Exception:
    pass
  return None


def text_color(hexc):
  r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
  return "#222" if r * 0.299 + g * 0.587 + b * 0.114 > 150 else "#fff"


def color_buttons_css(keys_and_colors):
  """צובע כפתורים (לפי key) בצבע האמיתי שלהם."""
  rules = [
      f".st-key-{k} button {{ background:{c} !important; color:{text_color(c)}"
      " !important; border-color:#ccc !important; }"
      for k, c in keys_and_colors if c
  ]
  if rules:
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


def big_card(emoji, english, hebrew, image_url=None, color=None):
  if image_url:
    pic = f'<img src="{image_url}" style="max-height:220px;border-radius:20px">'
  elif color:
    pic = (f'<div style="width:150px;height:150px;border-radius:50%;margin:8px auto;'
           f'background:{color};border:5px solid #fff;box-shadow:0 4px 14px #0003">'
           "</div>")
  else:
    pic = f'<div class="emo">{emoji}</div>'
  st.markdown(
      f'<div class="big-card">{pic}<div class="eng">{english}</div>'
      f'<div class="heb">{hebrew}</div></div>',
      unsafe_allow_html=True,
  )


# ---------------------------------------------------------------------------
# ניווט
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("page", "home")


def go(page, **values):
  ss.page = page
  for k, v in values.items():
    ss[k] = v
  # איפוס מצב המשחקים בכל מעבר מסך
  for k in [k for k in ss.keys() if str(k).startswith("g_")]:
    del ss[k]


def back_button(target, label="⬅️ חזרה"):
  st.button(label, on_click=go, args=(target,), key=f"back_{target}")


def items():
  """המילים של הקטגוריה + מילים שנוספו מ-AI."""
  return CATEGORIES[ss.category]["items"] + extra_items(ss.category)


CATEGORY_REQUESTS = {
    "animals": "animals", "colors": "colors and shades (include the hex code)",
    "objects": "everyday objects at home", "family": "family members and people",
    "classroom": "things in a classroom and school", "nature": "nature and weather",
    "food": "food, fruits and vegetables", "transport": "vehicles and transportation",
    "body": "parts of the body", "letters": "simple words, one per letter A-Z",
}


# ---------------------------------------------------------------------------
# משחקים
# ---------------------------------------------------------------------------
def game_cards():
  is_colors = ss.category == "colors"
  sel = ss.get("g_selected")
  if sel is not None:
    heb, eng, emo, hexc = unpack(items()[sel])
    big_card(emo, eng, heb, color=hexc)
    speak((heb, "iw"), (eng, "en"))
  else:
    st.info("👇 לחצו על תמונה כדי לשמוע אותה בעברית ובאנגלית")

  ncols = 3
  cols = st.columns(ncols)
  colored = []
  for i, it in enumerate(items()):
    heb, eng, emo, hexc = unpack(it)
    pic = "" if is_colors and hexc else emo
    if ss.age == "small":
      label = f"{pic}  {heb}"
    else:
      label = f"{pic} {heb} · {eng}"
    colored.append((f"card_{i}", hexc))
    with cols[i % ncols]:
      if st.button(label.strip(), key=f"card_{i}", use_container_width=True):
        ss.g_selected = i
        st.rerun()
  color_buttons_css(colored)

  st.markdown("---")
  st.caption(f"יש כאן {len(items())} מילים. רוצים עוד? ה-AI ימציא מילים חדשות בנושא!")
  ai_button(ss.category, CATEGORY_REQUESTS[ss.category], items())


def game_explore():
  """בחירת אות -> מילים שמתחילות בה."""
  # רשת האותיות משמאל לימין, כמו באנגלית
  st.markdown("<style>.st-key-abc_grid{direction:ltr}</style>",
              unsafe_allow_html=True)
  cols = st.container(key="abc_grid").columns(7)
  for i, letter in enumerate(ALPHABET):
    with cols[i % 7]:
      if st.button(letter, key=f"letter_{letter}", use_container_width=True):
        ss.g_letter = letter
        ss.g_word = None
        st.rerun()

  letter = ss.get("g_letter")
  if not letter:
    st.info("👆 בחרו אות כדי לראות מילים שמתחילות בה")
    return
  words = letter_words(letter)
  st.markdown(
      f"<div class='big-card'><div class='eng' style='font-size:110px'>"
      f"{letter} {letter.lower()}</div></div>",
      unsafe_allow_html=True,
  )
  word = ss.get("g_word")
  if word is not None and word < len(words):
    heb, eng, emo, hexc = unpack(words[word])
    big_card(emo, eng, heb, color=hexc)
    speak((eng, "en"), (heb, "iw"))
  else:
    sample = ", ".join(unpack(w)[1] for w in words[:3])
    speak((letter, "en"), (f"{letter} is for {sample}", "en"))

  st.markdown(f"#### מילים שמתחילות ב־{letter} ({len(words)}):")
  cols = st.columns(3)
  for i, it in enumerate(words):
    heb, eng, emo, _ = unpack(it)
    with cols[i % 3]:
      if st.button(f"{emo} {eng} · {heb}", key=f"lw_{i}", use_container_width=True):
        ss.g_word = i
        st.rerun()
  ai_button(f"letter_{letter}",
            f"simple English words that start with the letter {letter}",
            words, label=f"✨ עוד מילים באות {letter} מ-AI")


def game_abc():
  """תרגול כל האותיות לפי הסדר."""
  idx = ss.setdefault("g_abc", 0)
  letter = ALPHABET[idx]
  words = letter_words(letter)
  st.progress((idx + 1) / 26, text=f"אות {idx + 1} מתוך 26")
  st.markdown(
      f"<div class='big-card'><div class='eng' style='font-size:120px'>"
      f"{letter} {letter.lower()}</div>"
      f"<div style='font-size:60px'>{' '.join(unpack(w)[2] for w in words[:4])}</div>"
      f"<div class='eng' style='font-size:28px'>"
      f"{' · '.join(unpack(w)[1] for w in words[:4])}</div></div>",
      unsafe_allow_html=True,
  )
  sample = ", ".join(unpack(w)[1] for w in words[:3])
  speak((letter, "en"), (f"{letter} is for {sample}", "en"))

  c1, c2 = st.columns(2)
  with c1:
    if idx < 25 and st.button("הבאה ➡️", type="primary", use_container_width=True):
      ss.g_abc += 1
      st.rerun()
  with c2:
    if idx > 0 and st.button("⬅️ הקודמת", use_container_width=True):
      ss.g_abc -= 1
      st.rerun()
  if idx == 25:
    st.balloons()
    st.success("🏆 כל הכבוד! עברתם על כל האותיות מ-A עד Z!")
    if st.button("🔁 מההתחלה", use_container_width=True):
      ss.g_abc = 0
      st.rerun()


def new_letter_round():
  options = random.sample(ALPHABET, 4)
  ss.g_fl_options = options
  ss.g_fl_target = random.choice(options)
  ss.g_fl_result = None


def game_find_letter():
  ss.setdefault("g_score", 0)
  if "g_fl_target" not in ss:
    new_letter_round()
  target = ss.g_fl_target
  st.markdown(f"### ⭐ ניקוד: {ss.g_score}")
  st.markdown("<h2>🔊 איזו אות שמעתם?</h2>", unsafe_allow_html=True)
  if ss.g_fl_result != "win":
    speak((f"Where is the letter {target}?", "en"))

  cols = st.columns(4)
  for i, letter in enumerate(ss.g_fl_options):
    with cols[i]:
      if st.button(letter, key=f"fl_{i}", use_container_width=True):
        ss.g_fl_result = "win" if letter == target else "miss"
        ss.g_score += ss.g_fl_result == "win"
        st.rerun()

  if ss.g_fl_result == "win":
    st.balloons()
    words = letter_words(target)
    heb, eng, emo, hexc = unpack(words[0])
    big_card(emo, f"{target} — {eng}", heb, color=hexc)
    speak(("Great job!", "en"), (f"{target} is for {eng}", "en"))
    st.button("➡️ עוד אות!", on_click=new_letter_round, type="primary",
              use_container_width=True)
  elif ss.g_fl_result == "miss":
    st.warning("🙈 אופס! נסו שוב")


def new_find_round():
  options = random.sample(items(), k=min(4, len(items())))
  ss.g_find_options = options
  ss.g_find_target = random.choice(options)
  ss.g_find_result = None


def game_find():
  ss.setdefault("g_score", 0)
  if "g_find_target" not in ss:
    new_find_round()
  heb, eng, emo, hexc = unpack(ss.g_find_target)

  st.markdown(f"### ⭐ ניקוד: {ss.g_score}")
  st.markdown(
      f"<h2 style='direction:ltr'>Where is the <u>{eng}</u>? 🔍</h2>",
      unsafe_allow_html=True,
  )
  if ss.g_find_result != "win":
    speak((f"Where is the {eng}?", "en"))

  cols = st.columns(len(ss.g_find_options))
  colored = []
  for i, opt in enumerate(ss.g_find_options):
    oh, oe, oemo, ohex = unpack(opt)
    colored.append((f"opt_{i}", ohex))
    with cols[i]:
      if st.button("‎" if ohex else oemo, key=f"opt_{i}",
                   use_container_width=True):
        if oe == eng:
          ss.g_find_result = "win"
          ss.g_score += 1
        else:
          ss.g_find_result = "miss"
        st.rerun()
  color_buttons_css(colored)

  if ss.g_find_result == "win":
    st.balloons()
    big_card(emo, eng, heb, color=hexc)
    speak(("Great job!", "en"), (f"{eng}", "en"), (heb, "iw"))
    st.button("➡️ עוד אחד!", on_click=new_find_round, type="primary",
              use_container_width=True)
  elif ss.g_find_result == "miss":
    st.warning("🙈 אופס! נסו שוב")


def game_type():
  st.markdown("### ⌨️ הקלידו כל מילה בעברית")
  st.caption("💡 אפשר כל מילה בעולם: דינוזאור, חללית, ארמון, גלידה...")
  word = st.text_input("מילה בעברית:", key="g_type_word").strip()
  if not word:
    return

  if word in LOCAL_DICT:
    eng, emo = LOCAL_DICT[word]
    image = None
  else:
    with st.spinner("מתרגמים... ✨"):
      eng = translate_hebrew_to_english(word)
    emo = "✨"
    image = find_image(eng) if eng else None
  if not eng:
    st.error("לא הצלחנו לתרגם 😕 בדקו שהמילה כתובה נכון ושיש אינטרנט")
    return

  big_card(emo, eng, word, image)
  speak((word, "iw"), (eng, "en"))

  st.markdown("---")
  st.markdown("#### ✍️ עכשיו נסו לכתוב את המילה באנגלית:")
  guess = st.text_input("כתבו באנגלית:", key=f"g_type_guess_{word}")
  if guess:
    if guess.strip().lower() == eng.lower():
      st.balloons()
      st.success("🎉 מדהים! כתבתם נכון!")
    else:
      st.error(f"כמעט! נסו שוב 💪 (רמז: מתחיל ב־{eng[0]})")


def new_missing_round():
  heb, eng, emo, hexc = unpack(random.choice(items()))
  word = eng.upper()
  letter_pos = [i for i, c in enumerate(word) if c.isalpha()]
  n_hide = 1 if len(letter_pos) <= 3 else 2 if len(letter_pos) <= 6 else 3
  hidden = sorted(random.sample(letter_pos, n_hide))
  missing = [word[i] for i in hidden]
  extras = random.sample(
      [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in missing], 6 - n_hide
  )
  tiles = missing + extras
  random.shuffle(tiles)
  ss.g_miss = {"item": (heb, eng, emo, hexc), "word": word, "hidden": hidden,
               "filled": 0, "tiles": tiles, "msg": None}


def game_missing():
  ss.setdefault("g_score", 0)
  if "g_miss" not in ss:
    new_missing_round()
  g = ss.g_miss
  heb, eng, emo, hexc = g["item"]
  word, hidden = g["word"], g["hidden"]
  done = g["filled"] == len(hidden)

  st.markdown(f"### ⭐ ניקוד: {ss.g_score}")
  pic = (f"<div style='width:110px;height:110px;border-radius:50%;margin:auto;"
         f"background:{hexc};border:4px solid #ddd'></div>" if hexc
         else f"<div style='text-align:center;font-size:100px'>{emo}</div>")
  st.markdown(pic, unsafe_allow_html=True)
  st.markdown(f"<div style='text-align:center;font-size:24px'>{heb}</div>",
              unsafe_allow_html=True)

  shown = []
  for i, c in enumerate(word):
    if c == " ":
      shown.append("&nbsp;")
    elif i in hidden[g["filled"]:]:
      shown.append("<span class='gap'>_</span>")
    else:
      shown.append(c)
  st.markdown(f"<div class='puzzle'>{''.join(shown)}</div>", unsafe_allow_html=True)

  if done:
    st.balloons()
    st.success("🎉 כל הכבוד! הרכבתם את המילה!")
    speak(("Great job!", "en"), (eng, "en"))
    st.button("➡️ מילה חדשה", on_click=new_missing_round, type="primary",
              use_container_width=True)
    return

  st.write("👇 בחרו את האות החסרה הבאה:")
  cols = st.columns(len(g["tiles"]))
  for i, t in enumerate(g["tiles"]):
    with cols[i]:
      if st.button(t, key=f"tile_{i}_{t}", use_container_width=True):
        if t == word[hidden[g["filled"]]]:
          g["filled"] += 1
          g["tiles"].pop(i)
          g["msg"] = None
          if g["filled"] == len(hidden):
            ss.g_score += 1
        else:
          g["msg"] = "🙈 לא האות הזאת, נסו שוב!"
        st.rerun()
  if g["msg"]:
    st.warning(g["msg"])

  if st.button("🔊 רמז - שמעו את המילה"):
    speak((eng, "en"))


GAME_FUNCS = {"cards": game_cards, "find": game_find, "type": game_type,
              "missing": game_missing, "explore": game_explore,
              "abc": game_abc, "find_letter": game_find_letter}


# ---------------------------------------------------------------------------
# מסכים
# ---------------------------------------------------------------------------
def page_home():
  st.html(HERO)
  st.button("🚀 בואו נתחיל!", on_click=go, args=("age",), type="primary",
            use_container_width=True)


def page_age():
  st.markdown("## 👶 בן/בת כמה הילד/ה?")
  c1, c2 = st.columns(2)
  with c1:
    st.button("🧸\n\nגילאי 1-4\n\nמשחקי תמונות", on_click=go,
              args=("category",), kwargs={"age": "small"},
              use_container_width=True)
  with c2:
    st.button("🎒\n\nגילאי 5-8\n\nתמונות + הקלדה", on_click=go,
              args=("category",), kwargs={"age": "big"},
              use_container_width=True)
  back_button("home")


def page_category():
  st.markdown("## 📂 בחרו נושא")
  keys = list(CATEGORIES)
  cols = st.columns(3)
  for i, key in enumerate(keys):
    cat = CATEGORIES[key]
    with cols[i % 3]:
      st.button(f"{cat['emoji']}  {cat['name']}", key=f"cat_{key}",
                on_click=go, args=("menu",), kwargs={"category": key},
                use_container_width=True)
  back_button("age", "⬅️ החלפת גיל")


def page_menu():
  cat = CATEGORIES[ss.category]
  st.markdown(f"## {cat['emoji']} {cat['name']} — בחרו משחק")
  for gkey in games_for(ss.age, ss.category):
    emo, name, desc = GAMES[gkey]
    st.button(f"{emo}  {name}", key=f"game_{gkey}", on_click=go,
              args=("game",), kwargs={"game": gkey}, use_container_width=True,
              help=desc)
  back_button("category", "⬅️ נושא אחר")


def page_game():
  cat = CATEGORIES[ss.category]
  emo, name, _ = GAMES[ss.game]
  st.markdown(f"## {emo} {name} · {cat['emoji']} {cat['name']}")
  GAME_FUNCS[ss.game]()
  st.markdown("---")
  back_button("menu", "⬅️ משחק אחר")


{"home": page_home, "age": page_age, "category": page_category,
 "menu": page_menu, "game": page_game}[ss.page]()
