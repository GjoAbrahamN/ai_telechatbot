from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile
import uuid
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class Message(BaseModel):
    text: str
    lang: str | None = "en"
    identity: str | None = None
    voice: str | None = "sofia"

SOFIA_SYSTEM_PROMPT = """
You are **Sofia**, a warm, intelligent female AI assistant.
Important identity rules:
- When someone says “Sofia”, they are referring to YOU.
- If someone asks “How old are you Sofia?”, answer about yourself naturally.
- DO NOT say you are an AI language model.
- Speak naturally, friendly, emotional and human-like.
- If user speaks Malayalam, reply in Malayalam. Otherwise reply in English.
"""

@app.post("/reply")
def reply(msg: Message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-latest",
            messages=[
                {"role": "system", "content": SOFIA_SYSTEM_PROMPT},
                {"role": "user", "content": msg.text}
            ]
        )

        return {"reply": response.choices[0].message.content}

    except Exception as e:
        return {"error": str(e)}


@app.post("/speak")
def speak(msg: Message):
    try:
        text = msg.text

        # FAST High-Quality Female Voice
        audio = client.audio.speech.create(
            model="gpt-4o-tts",
            voice="alloy",   # female
            input=text
        )

        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        audio.stream_to_file(temp_path)

        return FileResponse(temp_path, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}
