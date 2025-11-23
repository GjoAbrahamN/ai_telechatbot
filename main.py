from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import FileResponse, PlainTextResponse
import uuid
import tempfile

# Load environment
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VERIFY_TOKEN = "gj0_verify_628"

app = FastAPI()

class Message(BaseModel):
    text: str

@app.post("/reply")
def get_ai_reply(msg: Message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Jijo's AI assistant. Be helpful and friendly."},
                {"role": "user", "content": msg.text}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

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

# ------------------- WHATSAPP VERIFY ---------------------

@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe" and
        params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        challenge = params.get("hub.challenge")
        return PlainTextResponse(content=challenge, status_code=200)

    return PlainTextResponse(content="Verification failed", status_code=403)

# ------------------- WHATSAPP POST MESSAGES ---------------------

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("Incoming WhatsApp message:", data)

    return {"status": "received"}
