from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import requests
import os
from utils.logger import logger
from datetime import datetime, timezone
from services.mongo_database import add_chat_message, get_company_from_user, get_whatsapp_credentials, update_message_whats_app_status

# Initialize the scheduler (ensure it's started only once)
executors = {
    'default': ThreadPoolExecutor(2)  # Increase from default (10) to 20
}
scheduler = BackgroundScheduler(executors=executors)
scheduler.start()

# WHATSAPP credentials saved
WHATSAPP_AUTH_TOKEN = os.getenv('WHATSAPP_AUTH_TOKEN')

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Function to send a WhatsApp message
def send_whatsapp_message(message_id, user_id, number, title_front, text_front):
    title = title_front.replace("\n", "")
    message = text_front.replace("\n", "").replace("\r", "")
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "template",
        "template": {
            "name": "general_dynamic_message",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [{"type": "text", "text": title}]
                },
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": message}]
                }
            ]
        }
    }

    if title == "chat_only":    
        payload["template"]["name"] = "text_dynamic_message"
        payload["template"]["components"] = [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": message}]
            }
        ]

    try:
        company_id = get_company_from_user(user_id)
        account_id = get_whatsapp_credentials(company_id)
        URL_WHATSAPP = f"https://graph.facebook.com/v21.0/{account_id}/messages"
        logger.info(f"Sending message to: {number}")
        response = requests.post(URL_WHATSAPP, headers=HEADERS, json=payload)
        if response.status_code == 200:
            json_response = response.json()
            logger.info(f"WHATSAPP: Message sent successfully {json_response}")
            update_message_whats_app_status(message_id, number, "delivered")
            status_msg = json_response['messages'][0].get("message_status")
            message_id_whatsApp = json_response['messages'][0].get("id")
            if title == "chat_only":
                add_chat_message(company_id, number, message, datetime.now(timezone.utc), False, status_msg, message_id_whatsApp)
            return {"status": "success", "message_sid": response.json()}
        else:
            logger.info(f"Message faild: {response.text}")
            return {"status": "failed", "error": response.text}
    except Exception as e:
        logger.error(str(e))
        return {"status": "failed", "error": str(e)}


# Function to schedule a WhatsApp message
def schedule_whatsapp_message(message_id, user_id, title, message, numbers, send_time):
    for number in numbers:
        scheduler.add_job(
            send_whatsapp_message,
            'date',
            run_date=send_time,
            args=[message_id, user_id, number, title, message],
            misfire_grace_time=30 
        )



