from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
import os
import time
import requests
import traceback
from fastapi.middleware.cors import CORSMiddleware
# from pymongo import MongoClient
from utils.token_management import refresh_token_task
from services.whatsapp import schedule_whatsapp_message, send_whatsapp_message
# from services.mongo_database import save_to_mongodb
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.chatgpt import ChatGpt, MODELS, PROMPT, SYSTEM_INSTRUCTION
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

load_dotenv()

logger = logging.getLogger("uvicorn")

# MongoDB connection settings
# CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
# DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME")
# COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")

# Connect to MongoDB
# client = MongoClient(CONNECTION_STRING)

# Access the database and collection
# database = client[DATABASE_NAME]
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

# scheduler = BackgroundScheduler()

# scheduler.add_job(
#     refresh_token_task,
#     trigger=IntervalTrigger(days=50),
#     id="refresh_token_task",
#     replace_existing=True
# )

# Start the scheduler
# scheduler.start()

# @app.on_event("shutdown")
# def shutdown_event():
#     scheduler.shutdown()

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
    userId: str
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
    image = request.image
    send_time_str = request.date

    try:
        # Parse the input UTC datetime string
        utc_datetime = datetime.strptime(send_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Assign UTC timezone to the parsed datetime
        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
        
        # Convert UTC datetime to Montevideo timezone (UTC-3)
        # montevideo_tz = pytz.timezone("America/Montevideo")
        # local_datetime = utc_datetime.astimezone(montevideo_tz)
    except ValueError as e:
        return {"error": f"Invalid date format. Expected in UTC format. Got: {send_time_str}"}

    if utc_datetime > datetime.now(timezone.utc):
        # Format the datetime as needed (optional)
        send_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
        schedule_whatsapp_message(title_msg, message, numbers, send_time)
        return {"status": "scheduled", "message": f"Message scheduled for {send_time}"}
    else:
    # Send message to each recipient
        response_list = []
        for number in numbers:
            result = send_whatsapp_message(number, title_msg, message)
            logger.info(f"Main: whatsapp result: {result}")
            response_list.append({"to": number, **result})
        return {"status": "sent", "results": response_list}

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

@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Parse the incoming JSON
        data = await request.json()

        # Handle statuses if provided in the payload
        statuses = data.get("statuses", [])
        for status in statuses:
            message_id = status.get("id")
            message_status = status.get("status")  # Example: 'read', 'delivered', etc.
            recipient_id = status.get("recipient_id")

            if message_status == "read":
                print(f"Message {message_id} to recipient {recipient_id} was read!")
        
        return {"status": "success"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}
