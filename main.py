from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import FileResponse
import uuid


# Load environment variables (.env)
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# Model for input JSON
class Message(BaseModel):
    text: str

@app.post("/reply")
def get_ai_reply(msg: Message):
    try:
        # Send prompt to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are Jijo's AI assistant. Be friendly, helpful, and natural."
                },
                {
                    "role": "user",
                    "content": msg.text
                }
            ]
        )
        
        # Extract AI response text (updated SDK format)
        reply_text = response.choices[0].message.content
        
        return {"reply": reply_text}

    except Exception as e:
        # If any error occurs, return it so we can debug
        return {"error": str(e)}
@app.post("/speak")
def speak_text(msg: Message):
    try:
        # Generate a temporary audio file name
        file_name = f"voice_{uuid.uuid4()}.mp3"
        file_path = f"./{file_name}"

        # Use OpenAI TTS (natural voice)
        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="verse",  # natural conversational voice
            input=msg.text
        )

        # Save audio file
        audio.stream_to_file(file_path)

        # Return the MP3 file to Flutter
        return FileResponse(file_path, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}
