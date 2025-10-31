from fastapi import FastAPI, Request
import requests
import os
import subprocess
from datetime import datetime

app = FastAPI()

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID_GROUP = os.getenv("CHAT_ID_GROUP")
RTSP_URL = os.getenv("RTSP_URL")

@app.get("/")
def root():
    return {"status": "online", "message": "SmartCam Railway is running 🚀"}

@app.get("/button")
def button_pressed():
    """Triggered when Shelly button is pressed"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"/tmp/snapshot_{timestamp}.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", RTSP_URL, "-frames:v", "1", filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        with open(filename, "rb") as photo:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID_GROUP, "caption": f"📸 Камера сработала в {timestamp}"},
                files={"photo": photo}
            )
        return {"status": "success", "message": "Photo sent!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates."""
    try:
        data = await request.json()
    except Exception:
        return {"ok": False}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    text = message.get("text", "")
    if not text:
        return {"ok": True}

    chat = message.get("chat", {})
    chat_id = chat.get("id")

    command = text.strip().split()[0].lower()
    if command.startswith("/cam"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"/tmp/snapshot_{timestamp}.jpg"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", RTSP_URL, "-frames:v", "1", filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            with open(filename, "rb") as photo:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={"chat_id": chat_id, "caption": f"📸 Камера сработала в {timestamp}"},
                    files={"photo": photo}
                )
        except Exception:
            pass

    return {"ok": True}
