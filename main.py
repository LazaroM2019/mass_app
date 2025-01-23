import base64
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel
import logging
import os
import time
import asyncio
import requests
import traceback
from fastapi.middleware.cors import CORSMiddleware
# from pymongo import MongoClient
from utils.token_management import refresh_token_task
from utils.general import batch_list
from services.whatsapp import download_media, schedule_whatsapp_message, update_business_image
from services.mongo_database import get_company_info, add_chat_message, get_whatsapp_credentials, update_wa_message_whats_app_status
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.chatgpt import ChatGpt, MODELS, PROMPT, SYSTEM_INSTRUCTION
from datetime import datetime, timezone, timedelta
import pytz
from dotenv import load_dotenv
from services.telegram import TelegramService
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

load_dotenv()

logger = logging.getLogger("uvicorn")
telegram_service = TelegramService()

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
    messageId: str
    doc: str

class AiSuggestion(BaseModel):
    title: str
    message: str

class CompanyImageRequest(BaseModel):
    companyId: str
    image: str

class MediaContentRequest(BaseModel):
    companyId: str
    media_id: str

# Route to send a WhatsApp message to multiple recipients
@app.post("/chat/send")
async def send_messages(request: MessageRequest):
    title_msg = request.title
    message = request.message
    numbers = request.numbers
    image = request.image
    user_id = request.userId
    send_time_str = request.date
    message_id = request.messageId
    doc_file = request.doc

    try:
        # Parse the input UTC datetime string
        utc_datetime = datetime.strptime(send_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Assign UTC timezone to the parsed datetime
        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
    except ValueError as e:
        return {"error": f"Invalid date format. Expected in UTC format. Got: {send_time_str}"}

    if utc_datetime > datetime.now(timezone.utc):
        # Format the datetime as needed
        send_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
        schedule_whatsapp_message(message_id, user_id, title_msg, message, numbers, send_time, image, doc_file)
        return {"status": "scheduled", "message": f"Message scheduled for {send_time}"}
    else:
    # Send message to each recipient
        batch_size = len(numbers)//5 or 1
        for batch in batch_list(numbers, batch_size):
            time_now = datetime.now(timezone.utc)
            logger.info(f"Manin BATCH: {batch}")
            schedule_whatsapp_message(message_id, user_id, title_msg, message, batch, time_now, image, doc_file)
            asyncio.sleep(4)
        return {"status": "sent", "message": f"Message sent"}

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
        logger.info("Webhook request")
        # Parse the incoming JSON
        data = await request.json()
        logger.info(f"Main: WEBHOOK REQUEST: {data}")

        # Handle statuses if provided in the payload
        statuses = data.get("entry", [])
        for status in statuses:
            changes = status.get("changes")[0]["value"]
            if "statuses" in list(changes.keys()):
                update_status = changes["statuses"][0].get("status")
                message_waid = changes["statuses"][0].get("id")
                phone_number_client = changes["statuses"][0].get("recipient_id")
                logger.info(f"Client Number: {phone_number_client}")
                logger.info(f"Webhook Status: {update_status}")
                if message_waid:            
                    update_wa_message_whats_app_status(message_waid, phone_number_client, update_status)
                    logger.info(f"Main: UPDATE STATUS for message_id: {message_waid}.")
                else:
                    logger.error(f"Main: Failed to update status for message_id: {message_waid}; we couldn't retrieve it.")
            if "messages" in list(changes.keys()):
                logger.info("new message")
                client_name = changes.get("contacts")[0].get("profile").get("name") 
                messages = changes.get("messages")[0]
                phone_number_bot = changes.get("metadata").get("display_phone_number")
                phone_number_client = messages.get("from")
                whatsapp_message_id = messages.get("id")
                msg_type = messages.get("type")
                media_id = None

                if msg_type == "text":
                    message = messages.get("text").get("body")
                    logger.info(f"message: {message} to: {phone_number_client}")
                
                elif msg_type in ["image", "document"]:
                    media = messages.get(msg_type, {})
                    message = media.get("caption", "")
                    media_id = media.get("id")
                    logger.info(f"message: {message} to: {phone_number_client} with media: {msg_type}")
                
                if len(message) > 0 or media_id != None:
                    company_id = get_company_info(phone_number_bot, "phone", "id")
                    logger.info(f"company: {company_id}")
                    if company_id:
                        add_chat_message(company_id, phone_number_client, message, datetime.now(timezone.utc), True, 'delivered', whatsapp_message_id, client_name, media_id, msg_type)

        
        return {"status": "success"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        telegram_service.send_message("Webhook Error")
        return {"status": "error", "message": str(e)}
    

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    VERIFY_TOKEN = "2rHZurQoDiVDJR48WooJJeZFVN2_2rStqXtnSs2iGb2QwAS9o"
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)  # Respond with the challenge string
    return {"error": "Verification failed"}


@app.put("/company/image")
async def update_company_image(request: CompanyImageRequest):
    company_id = request.companyId
    image = request.image

    update_business_image(company_id, image)

@app.get("/company/{company_id}/media/{media_id}")
async def get_media_content(company_id: str, media_id: str):

    account_id = get_whatsapp_credentials(company_id)
    logger.info(f"downloading image for: {account_id} - {media_id}")

    media_content = download_media(media_id, account_id)
    
    base64_encoded = base64.b64encode(media_content).decode("utf-8")
    
    return {"base64_data": base64_encoded}
