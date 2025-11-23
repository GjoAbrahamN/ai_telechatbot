from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
from openai import OpenAI
import uuid
import tempfile
from fastapi.responses import FileResponse

app = FastAPI()

VERIFY_TOKEN = "gj0_verify_628"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Message(BaseModel):
    text: str


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Verification failed"}


@app.post("/webhook")
async def receive_whatsapp(request: Request):
    data = await request.json()
    print("Incoming WhatsApp message:", data)
    return {"status": "received"}


@app.post("/reply")
async def send_reply(msg: Message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Jijo's AI assistant."},
            {"role": "user", "content": msg.text}
        ]
    )
    return {"reply": response.choices[0].message.content}


@app.post("/speak")
async def speak(msg: Message):
    file_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")

    audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="verse",
        input=msg.text
    )

    audio.stream_to_file(file_path)
    return FileResponse(file_path, media_type="audio/mpeg")
