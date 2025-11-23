from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import FileResponse
import uuid
import tempfile

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# WhatsApp verification token
VERIFY_TOKEN = "gj0_verify_628"   # Use the exact token you entered in Meta dashboard

app = FastAPI()


# ------------------------------
# MODELS
# ------------------------------

class Message(BaseModel):
    text: str


# ------------------------------
# AI TEXT REPLY
# ------------------------------

@app.post("/reply")
def get_ai_reply(msg: Message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Jijo's AI assistant. Be natural and helpful."},
                {"role": "user", "content": msg.text}
            ]
        )
        reply_text = response.choices[0].message.content
        return {"reply": reply_text}

    except Exception as e:
        return {"error": str(e)}


# ------------------------------
# AI VOICE REPLY (MP3)
# ------------------------------

@app.post("/speak")
def speak_text(msg: Message):
    try:
        temp_dir = tempfile.gettempdir()
        file_name = f"voice_{uuid.uuid4()}.mp3"
        file_path = os.path.join(temp_dir, file_name)

        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="verse",
            input=msg.text
        )
        audio.stream_to_file(file_path)

        return FileResponse(file_path, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}


# ------------------------------
# WHATSAPP WEBHOOK VERIFICATION (GET)
# ------------------------------

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Invalid verification token"}


# ------------------------------
# WHATSAPP MESSAGE RECEIVER (POST)
# ------------------------------

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("🔥 Incoming WhatsApp message:", data)

    # Always return 200 OK or WhatsApp will retry
    return {"status": "received"}
