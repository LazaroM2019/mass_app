from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
from utils.logger import logger

# Initialize the scheduler (ensure it's started only once)
scheduler = BackgroundScheduler()
scheduler.start()

# WHATSAPP credentials saved
WHATSAPP_ACCOUNT_SID = os.getenv('WHATSAPP_ACCOUNT_SID')
WHATSAPP_AUTH_TOKEN = os.getenv('WHATSAPP_AUTH_TOKEN')

# WHATSAPP API ENDPOINT
URL_WHATSAPP = f"https://graph.facebook.com/v21.0/{WHATSAPP_ACCOUNT_SID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Function to send a WhatsApp message
def send_whatsapp_message(number, title_front, text_front):
    title = title_front.replace("\n", "")
    message = text_front.replace("\n", "").replace("\r", "")
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "template",
        "template": {
            "name": "dynamic_params",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [{"type": "text","text": title}]
                },
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": message}]
                }
                ]
        }
    }
    try:
        response = requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)
        if response.status_code == 200:
            return {"status": "success", "message_sid": response.json()}
        else:
            return {"status": "failed", "error": response.text}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# def send_whatsapp_message(number, formatted_message, image_base64=None, caption=None):
#     # Build the payload based on whether an image is provided
#     if image_base64 is not None:
#         payload = {
#             "messaging_product": "whatsapp",
#             "to": number,
#             "type": "image",
#             "image": {
#                 "data": image_base64,  # Base64-encoded image data
#                 "caption": caption or formatted_message  # Use caption or formatted_message as a fallback
#             }
#         }
#     else:
#         payload = {
#             "messaging_product": "whatsapp",
#             "to": number,
#             "type": "text",
#             "text": {"body": formatted_message}
#         }
    
#     try:
#         response = requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)
#         if response.status_code == 200:
#             return {"status": "success", "message_sid": response.json()}
#         else:
#             return {"status": "failed", "error": response.text}
#     except Exception as e:
#         return {"status": "failed", "error": str(e)}


# Function to schedule a WhatsApp message
def schedule_whatsapp_message(title, message, numbers, send_time):
    formatted_message = f"*{title}*\n\n{message}"
    for number in numbers:
        scheduler.add_job(
            send_whatsapp_message,
            'date',
            run_date=send_time,
            args=[number, title, message]
        )

# Function to schedule a WhatsApp message
# def schedule_whatsapp_message(title, message, numbers, send_time, image_base64=None, caption=None):
#     # Format the message
#     formatted_message = f"*{title}*\n\n{message}"
    
#     for number in numbers:
#         # Schedule the send_whatsapp_message function with appropriate arguments
#         scheduler.add_job(
#             send_whatsapp_message,
#             'date',
#             run_date=send_time,
#             args=[number, formatted_message, image_base64, caption]
#         )
#     print(f"Message scheduled for {len(numbers)} recipient(s) at {send_time}")

