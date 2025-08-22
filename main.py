# main.py (Updated for Render Deployment)

import os # --- CHANGE 1: Added 'os' to read environment variables
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
import requests
import json
from pyzbar.pyzbar import decode as zbar_decode

app = FastAPI()

# ----------------- CORS CONFIG -----------------
# Get your Render URL after your first deployment (e.g., "https://your-app-name.onrender.com")
# and add it to this list for better security. Using "*" is okay for development.
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4943",
    "http://127.0.0.1:4943",
    "*" # --- CHANGE 2: Added "*" to allow requests from your future Render URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- CONFIG -----------------
# --- CHANGE 3: Securely load API Key from Render's Environment Variables
API_KEY = os.environ.get("API_KEY") 

# ----------------- HELPERS -----------------
def frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def decode_with_pyzbar(frame):
    decoded_objects = zbar_decode(frame)
    ids = [obj.data.decode('utf-8') for obj in decoded_objects]
    return ids

# --- CHANGE 4: The decode_with_gemini function is now passed the API_KEY
def decode_with_gemini(frame, api_key):
    # Add a check in case the API key wasn't set in the environment
    if not api_key:
        print("Error: Gemini API key is not set.")
        return []
        
    try:
        encoded_string = frame_to_base64(frame)

        headers = {"Content-Type": "application/json"}
        prompt = (
            "You are a highly specialized and accurate barcode and QR code scanner. "
            "Your sole purpose is to read the alphanumeric ID contained within the code in the image. "
            "You must return only the raw ID, with absolutely no other text, explanations, punctuation, or formatting. "
            "If the image contains a code, provide its ID. If no code is found, respond with nothing."
        )

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": encoded_string
                            }
                        }
                    ]
                }
            ]
        }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-pro-vision:generateContent?key={api_key}" # Using gemini-pro-vision as it's a stable model
        )

        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        result = response.json()

        if (
            "candidates" in result
            and len(result["candidates"]) > 0
            and "content" in result["candidates"][0]
            and "parts" in result["candidates"][0]["content"]
            and len(result["candidates"][0]["content"]["parts"]) > 0
            and "text" in result["candidates"][0]["content"]["parts"][0]
        ):
            text_part = result["candidates"][0]["content"]["parts"][0]["text"]
            clean_id = text_part.strip().replace("`", "").replace("json", "").replace("\n", "")
            if clean_id:
                return [clean_id]

    except Exception as e:
        print(f"Gemini API error: {e}")

    return []

# ----------------- ENDPOINTS -----------------
@app.get("/")
def health_check():
    """A simple endpoint to check if the service is live."""
    return {"status": "OK", "message": "Medi-Verify Scanner API is running."}

@app.post("/scan-image")
async def scan_image(file: UploadFile):
    """Receives an uploaded image, decodes it with Pyzbar first, Gemini if needed."""
    image_bytes = await file.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"success": False, "id": None, "all_ids": [], "message": "Could not decode image."}

    ids = decode_with_pyzbar(frame)

    if not ids:
        ids = decode_with_gemini(frame, API_KEY) # Pass the API key here

    if not ids:
        return {"success": False, "id": None, "all_ids": [], "message": "No QR code found in the image."}

    return {"success": True, "id": ids[0], "all_ids": ids}

# --- CHANGE 5: Removed the /scan-live endpoint ---
# This function cannot work on a server as it has no webcam.
# This functionality must be implemented in your frontend JavaScript code.
