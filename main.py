from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
import os
import time
import requests
import traceback
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from utils.token_management import refresh_token_task
from services.mongo_database import save_to_mongodb
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.chatgpt import ChatGpt, MODELS, PROMPT, SYSTEM_INSTRUCTION
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

load_dotenv()

logger = logging.getLogger("uvicorn")

# Twilio credentials (replace with your own Twilio credentials)
WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
WHATSAPP_AUTH_TOKEN = os.getenv('WHATSAPP_AUTH_TOKEN')

# WHATSAPP API ENDPOINT
URL_WHATSAPP = f"https://graph.facebook.com/v21.0/{WHATSAPP_ACCOUNT_SID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# MongoDB connection settings
CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")

# Connect to MongoDB
client = MongoClient(CONNECTION_STRING)

# Access the database and collection
database = client[DATABASE_NAME]
# collection = database[COLLECTION_NAME]


# FastAPI app
app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"]
)

scheduler = BackgroundScheduler()

scheduler.add_job(
    refresh_token_task,
    trigger=IntervalTrigger(days=50),
    id="refresh_token_task",
    replace_existing=True
)

# Start the scheduler
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request method, URL, and headers
    logger.info(f"Request: {request.method} {request.url}")
    
    # Log request body (input data)
    body = await request.body()
    logger.info(f"Request Body: {body.decode('utf-8')}")
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log response status code and processing time
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Process time: {process_time:.4f} seconds")
    
    return response


# Pydantic model for request body
class MessageRequest(BaseModel):
    title: str
    message: str
    numbers: list[str]  # List of recipient phone numbers
    userId: int
    image: str
    date: str

class AiSuggestion(BaseModel):
    title: str
    message: str

# Route to send a WhatsApp message to multiple recipients
@app.post("/chat/send")
async def send_messages(request: MessageRequest):
    title_msg = request.title
    message = request.message
    numbers = request.numbers
    
    # Send message to each recipient
    response_list = []
    for number in numbers:
        try:
            formatted_message = f"*{title_msg}*\n\n{message}"
            payload = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "text",
                "text": {
                    "body": formatted_message
                }
            }
            # send the request
            response = requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)

            if response.status_code == 200:
                logger.info(response.json())
                response_list.append({
                    "to": number,
                    "status": "success",
                    "message_sid": response.json()
                })
                # save_message_to_mongodb(collection,formatted_message)
            else:
                logger.error(f"Failed to send message to {number}: {response.text}")
                response_list.append({
                    "to": number,
                    "status": "failed",
                    "error": response.text
                })
        except Exception as e:
            traceback.print_exc()
            response_list.append({
                "to": number,
                "status": "failed",
                "error": str(e)
            })

    return {"results": response_list}

# Route to send a WhatsApp message to improved with ChatGpt
@app.post("/ai/suggestion")
async def chat_suggestion(request: AiSuggestion):
    title_msg = request.title
    message = request.message

    chat = ChatGpt(MODELS['GPT_4O_mini'], SYSTEM_INSTRUCTION)

    prompt = PROMPT.replace("__TEXT_TITLE__", title_msg)
    prompt = prompt.replace("__TEXT_MESSAGE__", message)

    outputs = chat.generate(prompt=prompt, respose_format=AiSuggestion)

    return outputs
