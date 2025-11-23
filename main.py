from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import FileResponse
import uuid
import tempfile
import re
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# Global memory for user name
USER_NAME = None

class Message(BaseModel):
    text: str

def detect_language(text: str):
    # Simple Malayalam detection
    mal_chars = "[\u0D00-\u0D7F]"
    if re.search(mal_chars, text):
        return "ml"
    return "en"

def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"

@app.post("/reply")
def get_ai_reply(msg: Message):
    global USER_NAME

    user_text = msg.text.lower().strip()

    # 1️⃣ Wake-word check
    if "sofia" not in user_text:
        return {"reply": ""}  # Ignore if wake word missing

    # 2️⃣ Extract main message (remove "sofia")
    cleaned = re.sub(r"\bsofia\b", "", msg.text, flags=re.IGNORECASE).strip()

    # 3️⃣ Detect language
    lang = detect_language(msg.text)

    # 4️⃣ Name learning
    if USER_NAME is None:
        # Ask name if not known
        USER_NAME = None
        if lang == "en":
            return {"reply": f"{greeting()}, I'm Sofia. May I know your name?"}
        else:
            return {"reply": "സുപ്രഭാതം‌, ഞാൻ സോഫിയയാണ്‌. താങ്കളുടെ പേര് പറയാമോ?"}

    # If user says "my name is ..."
    match = re.search(r"(my name is|എന്റെ പേര്)\s+([A-Za-z\u0D00-\u0D7F]+)", msg.text, re.IGNORECASE)
    if match:
        USER_NAME = match.group(2)
        if lang == "en":
            return {"reply": f"Nice to meet you, {USER_NAME}! How can I help you?"}
        else:
            return {"reply": f"{USER_NAME}, കണ്ടതിൽ സന്തോഷം! എനിക്ക് എങ്ങനെ സഹായിക്കാം?"}

    # 5️⃣ AI Conversation
    system_prompt_en = (
        f"You are Sofia, a friendly female AI assistant. "
        f"The user's name is {USER_NAME}. Respond warmly, naturally, and helpfully."
    )

    system_prompt_ml = (
        f"നീ സോഫിയയാണ്‌, ഒരു സുഹൃദ സ്വഭാവമുള്ള വനിതാ AI അസിസ്റ്റന്റ്. "
        f"ഉപയോക്താവിന്റെ പേര് {USER_NAME}. വളരെ സ്വാഭാവികവും സൗഹൃദപരവുമായും മറുപടി നൽകുക."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt_ml if lang == "ml" else system_prompt_en},
            {"role": "user", "content": cleaned}
        ]
    )

    reply_text = response.choices[0].message.content
    return {"reply": reply_text}

@app.post("/speak")
def speak_text(msg: Message):
    try:
        # Create TEMP FILE for Render
        temp_dir = tempfile.gettempdir()
        file_name = f"voice_{uuid.uuid4()}.mp3"
        file_path = os.path.join(temp_dir, file_name)

        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="verse",   # best female natural voice
            input=msg.text
        )

        audio.stream_to_file(file_path)

        return FileResponse(file_path, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}
