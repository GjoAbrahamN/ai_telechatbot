from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import FileResponse
import uuid
import tempfile
from fastapi import Request


# Load .env
load_dotenv()

# Initialize OpenAI Client using Render Environment Variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VERIFY_TOKEN = "gj0_verify_628"   # <-- you can change this

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
        reply_text = response.choices[0].message.content
        return {"reply": reply_text}
    except Exception as e:
        return {"error": str(e)}

@app.post("/speak")
def speak_text(msg: Message):
    try:
        # Create TEMP FILE (best for Render)
        temp_dir = tempfile.gettempdir()
        file_name = f"voice_{uuid.uuid4()}.mp3"
        file_path = os.path.join(temp_dir, file_name)

        # Generate voice file
        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="verse",
            input=msg.text
        )

        # Save mp3
        audio.stream_to_file(file_path)

        # Return the mp3 file
        return FileResponse(file_path, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}

@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))

    return {"error": "Verification failed"}

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("Incoming WhatsApp message:", data)

    # return 200 OK to avoid WhatsApp errors
    return {"status": "received"}