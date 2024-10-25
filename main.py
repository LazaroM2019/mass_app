from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from twilio.rest import Client
import logging
import os
import time
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("uvicorn")

# Twilio credentials (replace with your own Twilio credentials)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Twilio WhatsApp sandbox number

# Initialize the Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# FastAPI app
app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"]
)

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
    message: str
    numbers: list[str]  # List of recipient phone numbers

class EventRequest(BaseModel):
    date_event: str
    hora_event: str
    numbers: list[str] 

# Route to send a WhatsApp message to multiple recipients
@app.post("/send-messages/")
async def send_messages(request: MessageRequest):
    message = request.message
    numbers = request.numbers
    
    # Send message to each recipient
    response_list = []
    for number in numbers:
        number_cell = f"+{number.lstrip('+')}"
        try:
            message_response = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=message,
                to=f'whatsapp:{number_cell}'  # Send as WhatsApp message
            )
            response_list.append({
                "to": number_cell,
                "status": "success",
                "message_sid": message_response.sid
            })
        except Exception as e:
            response_list.append({
                "to": number_cell,
                "status": "failed",
                "error": str(e)
            })

    return {"results": response_list}

@app.post("/send-markrting-campagne/")
async def send_messages(request: EventRequest):
    str_date = request.date_event
    str_hora = request.hora_event
    list_numbers = request.numbers

    response_list = []
    for number in list_numbers:
        number_cell = f"+{number.lstrip('+')}"
        try:
            message_response = client.messages.create(
                    from_='whatsapp:+14155238886',
                    content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
                    content_variables='{"1":"%s","2":"%s"}' %(str(str_date),str(str_hora)),
                    to=f'whatsapp:{number_cell}'
                    )
            response_list.append({
                "to": number_cell,
                "status": "success",
                "message_sid": message_response.sid
            })
        except Exception as e:
            response_list.append({
                "to": number_cell,
                "status": "failed",
                "error": str(e)
            })

    return {"results": response_list}
