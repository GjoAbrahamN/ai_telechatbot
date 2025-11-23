from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import OpenAI
import tempfile
import uuid
import os

# Load env variables
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# WhatsApp webhook verify token
VERIFY_TOKEN = "gj0_verify_628"

app = FastAPI()


# ---------------------------
#  DATA MODELS
# ---------------------------
class Message(BaseModel):
    text: str


# ---------------------------
#   TEXT → AI REPLY
# ---------------------------
@app.post("/reply")
def get_ai_reply(msg: Message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Sofia, a friendly AI voice assistant. "
                        "Speak naturally like a human. Reply shortly and clearly."
                    )
                },
                {
                    "role": "user",
                    "content": msg.text
                }
            ]
        )

        reply_text = response.choices[0].message.content
        return {"reply": reply_text}

    except Exception as e:
        return {"error": str(e)}


# ---------------------------
#   AI REPLY → VOICE (TTS)
# ---------------------------
@app.post("/speak")
def speak_text(msg: Message):
    try:
        # Temp directory (Safe for Render)
        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, f"voice_{uuid.uuid4()}.mp3")

        # Generate AI voice using TTS
        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="verse",   # natural conversational female-like
            input=msg.text
        )

        # Save voice file
        audio.stream_to_file(file_path)

        # Return file
        return FileResponse(file_path, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}


# ---------------------------
#  WHATSAPP WEBHOOK VERIFY
# ---------------------------
@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params.get("hub.challenge"))

    return {"error": "Verification failed"}


# ---------------------------
#  WHATSAPP MESSAGE RECEIVER
# ---------------------------
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("📩 Incoming WhatsApp Message:", data)

    # Always return 200 OK
    return {"status": "received"}
